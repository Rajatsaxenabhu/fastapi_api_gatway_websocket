import httpx
from fastapi import Request, Response, status, WebSocket, UploadFile,WebSocketDisconnect
from typing import List, Optional, Dict, Any, Union, Callable
from importlib import import_module
import base64
from pydantic import BaseModel
import functools
from starlette.datastructures import UploadFile as StarletteUploadFile
from urllib.parse import urlparse, urlunparse
from httpx_ws import aconnect_ws
import json

class APIError(Exception):
    def __init__(self, status_code: int, detail: str, headers: Optional[Dict[str, str]] = None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}
        super().__init__(detail)

class RequestError(APIError):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class AuthenticationError(APIError):
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class Client:
    async def http_request(
        self,
        url: str,
        method: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> tuple[Any, int]:
        headers = headers or {}
        params = params or {}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    json=data,
                    headers=headers,
                    params=params,
                    timeout=timeout
                )
                response.raise_for_status()
                return response.json(), response.status_code
            except httpx.HTTPStatusError as e:
                raise APIError(
                    status_code=e.response.status_code,
                    detail=str(e)
                )
            except Exception as e:
                raise APIError(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

def route_rest(
    request_method: Any,
    path: str,
    service_url: str,
    authentication_required: bool = False,
    form_data: bool = False,
    status_code: Optional[int] = None,
    payload_key: Optional[str] = None,
):

    real_link = request_method(
        path,
        status_code=status_code
    )
    client = Client()


    def wrapper(func):
        @real_link
        @functools.wraps(func)
        async def inner(request: Request, response: Response=None, **kwargs):           
            try:
                method = request.method.lower()
                url = f'{service_url}{request.url.path}'
                payload = await process_payload(payload_key, kwargs, form_data)
                query_params = dict(request.query_params)
                
                resp_data, status_code_from_service = await client.http_request(
                    url=url,
                    method=method,
                    data=payload,
                    headers={},
                    params=query_params
                )
                response.status_code = status_code_from_service
                return resp_data

            except APIError:
                raise
            except Exception:
                raise APIError(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                )

        return inner
    return wrapper

async def process_payload(payload_key: str, kwargs: Dict[str, Any], form_data: bool = False) -> Optional[Any]:
    try:
        if not kwargs:
            return {} if form_data else None
            
        payload_obj = kwargs.get(payload_key)
        
        if not payload_obj:
            if form_data:
                return await process_form_data(kwargs)
            return kwargs

        if form_data:
            if isinstance(payload_obj, dict):
                return await process_form_data(payload_obj)
            return await process_form_data(kwargs)
        
        return (
            payload_obj.model_dump() 
            if isinstance(payload_obj, BaseModel) 
            else payload_obj
        )
        
    except Exception as e:
        if form_data:
            return {}
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing payload: {str(e)}"
        )

async def process_form_data(data: Dict) -> Dict:
    if not data:
        return {}
        
    processed_data = {}
    for key, value in data.items():
        if isinstance(value, list):
            processed_data[key] = []
            
            if not value:
                continue
                
            if any(isinstance(f, (UploadFile, StarletteUploadFile)) for f in value):
                for file in value:
                    if not isinstance(file, (UploadFile, StarletteUploadFile)):
                        continue
                    try:
                        file_content = await file.read()
                        await file.seek(0)
                        processed_data[key].append({
                            'filename': file.filename,
                            'content': base64.b64encode(file_content).decode('utf-8'),
                            'content_type': file.content_type or 'application/octet-stream'
                        })
                    except Exception:
                        continue
            else:
                processed_data[key] = value
                
        elif isinstance(value, (UploadFile, StarletteUploadFile)):
            try:
                file_content = await value.read()
                await value.seek(0)
                processed_data[key] = {
                    'filename': value.filename,
                    'content': base64.b64encode(file_content).decode('utf-8'),
                    'content_type': value.content_type or 'application/octet-stream'
                }
            except Exception:
                processed_data[key] = None
                
        elif isinstance(value, str):
            processed_data[key] = value
            
        elif value is None:
            processed_data[key] = None
            
        elif isinstance(value, BaseModel):
            processed_data[key] = value.model_dump()
            
        else:
            processed_data[key] = value
            
    return processed_data

#s

class SimpleWebSocketProxy:
    def __init__(self, service_url: str,path:str):
        self.ws_url = f"ws://{service_url}{path}"
        print(f"Target WebSocket URL: {self.ws_url}")

    async def handle_message(self, data: Dict[str, Any], ws, client_ws: WebSocket):
        try:
            if "text" in data:
                try:
                    json_data = json.loads(data["text"])
                    await ws.send_json(json_data)
                    response = await ws.receive_text()
                    await client_ws.send_text(response)
                except json.JSONDecodeError:
                    await ws.send_text(data["text"])
                    response = await ws.receive_text()
                    await client_ws.send_text(response)
                    
            elif "bytes" in data:
                await ws.send_bytes(data["bytes"])
                response = await ws.receive_bytes()
                await client_ws.send_bytes(response)
                
            else:
                error_msg = f"Unsupported message format: {data}"
                await client_ws.send_json({
                    "type": "error",
                    "error": error_msg
                })
                
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            await client_ws.send_json({
                "type": "error",
                "error": error_msg
            })

    async def proxy(self, client_ws: WebSocket):
        """Main proxy method to handle WebSocket connections"""
        print("Starting websocket proxy")
        await client_ws.accept()
        print("Client connection accepted")

        async with httpx.AsyncClient() as client:
            try:
                async with aconnect_ws(self.ws_url, client) as ws:
                    print("Connected to target service")
                    while True:
                        try:
                            data = await client_ws.receive()
                            print(f"Received message: {data}")
                            await self.handle_message(data, ws, client_ws)
                            
                        except WebSocketDisconnect:
                            print("Client disconnected")
                            break
                        except Exception as e:
                            print(f"Error in message handling: {str(e)}")
                            try:
                                await client_ws.send_json({
                                    "type": "error",
                                    "error": str(e)
                                })
                            except:
                                pass
                            break
                            
            except Exception as e:
                print(f"Connection error: {str(e)}")
                try:
                    await client_ws.close(code=1011)
                except:
                    pass  
def route_ws(
    path: str,
    service_url: str,
    authentication_required: bool = False,
):
    pass
    async def websocet_wrapper(func):
        async def inner(websocket:WebSocket):
            print("New websocket connection request")
            #tae the header 
            #try auth
            try:
                #auth
                pass
            except Exception as e:
                print("filaoed under auth")
                pass
            try:
                proxy = SimpleWebSocketProxy(service_url,path)
                await proxy.proxy(websocket)
            except Exception as e:
                print(f"WebSocket error: {str(e)}")
                try:
                    await websocket.close(code=1011)
                except:
                    pass
        return inner
    return websocet_wrapper
