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
    def __init__(self, service_url: str):
        self.ws_url = service_url
        print(f"Initializing proxy to connect to: {self.ws_url}")

    async def proxy(self, client_ws: WebSocket):
        try:
            await client_ws.accept()
            
            async with httpx.AsyncClient() as client: 
                try:
                    async with aconnect_ws(self.ws_url, client) as ws:
                        while True:
                            try:
                                # Receive and handle different message types from client
                                data = await client_ws.receive()
                                
                                # Handle different message types
                                if 'text' in data:
                                    message=data['text']
                                    await ws.send_text(message)

                                elif 'bytes' in data:
                                    message=data['bytes']
                                    await ws.send_bytes(message)
                                   
                                elif 'json' in message:
                                    message=data['json']
                                    await ws.send_json(message)
                        
                                
                                # Receive response from service
                                response = await ws.receive()
                                
                                # Forward response back to client
                                if isinstance(response, str):
                                    await client_ws.send_text(response)
                                elif isinstance(response, bytes):
                                    await client_ws.send_bytes(response)
                                elif isinstance(response, dict):
                                    await client_ws.send_json(response)
                                    
                            except WebSocketDisconnect:
                                print("Client disconnected")
                                break
                            except Exception as e:
                                print(f"Message handling error: {str(e)}")
                                await client_ws.send_json({
                                    "type": "error",
                                    "error": str(e)
                                })
                                break
                except httpx.ConnectError as e:
                    print(f"Service connection refused: {self.ws_url}")
                    print(f"Detailed error: {str(e)}")
                    await client_ws.send_json({
                        "type": "error",
                        "error": "Service connection refused",
                        "details": str(e)
                    })
                    
                except Exception as e:
                    print(f"Service connection error: {str(e)}")
                    await client_ws.send_json({
                        "type": "error",
                        "error": str(e)
                    })
                
                finally:
                    try:
                        await client_ws.close()
                    except:
                        pass 

        except Exception as e:
            print(f"Client connection error: {str(e)}")
            try:
                await client_ws.close(code=1011)
            except:
                pass

def route_ws(
        request_methods:Any,
        path: str, 
        service_url: str, 
        authentication_required: bool = False):

        def websocket_wrapper(func):
            @request_methods(path)
            async def inner(websocket: WebSocket):
                try:
                    print(f"Attempting to establish proxy to {service_url}")  # Debug log
                    proxy = SimpleWebSocketProxy(service_url)  # Use provided service_url
                    await proxy.proxy(websocket)
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    try:
                        await websocket.close(code=1011)
                    except:
                        pass
            return inner
        return websocket_wrapper