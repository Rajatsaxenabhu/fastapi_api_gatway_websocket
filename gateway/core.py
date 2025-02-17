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


class SimpleWebSocketProxy:
    def __init__(self, target_url: str):
        parsed = urlparse(target_url)
        # Using the target URL properly
        self.ws_url = f"ws://{parsed.netloc}{parsed.path}"
        print(f"Target WebSocket URL: {self.ws_url}")

    async def proxy(self, client_ws: WebSocket):
        print("Starting websocket proxy")
        await client_ws.accept()
        print("Client connection accepted")

        async with httpx.AsyncClient() as client:
            try:
                # Connect to target service using httpx_ws
                print(f"Connecting to target: {self.ws_url}")
                async with aconnect_ws(self.ws_url, client) as ws:
                    print("Connected to target service")
                    
                    while True:
                        try:
                            # Get message from client
                            data = await client_ws.receive()
                            msg_type = data.get("type")
                            print(f"Received message type: {msg_type}")
                            
                            # Forward to service
                            if "text" in data:
                                message = data["text"]
                                print(f"Forwarding text: {message}")
                                await ws.send_text(message)
                                
                                # Get and forward response
                                response = await ws.receive_text()
                                await client_ws.send_text(response)
                                
                            elif "bytes" in data:
                                message = data["bytes"]
                                print(f"Forwarding binary data")
                                await ws.send_bytes(message)
                                
                                # Get and forward response
                                response = await ws.receive_bytes()
                                await client_ws.send_bytes(response)
                                
                        except WebSocketDisconnect:
                            print("Client disconnected")
                            break
                        except Exception as e:
                            print(f"Error in message handling: {str(e)}")
                            break
                            
            except Exception as e:
                print(f"Connection error: {str(e)}")
                try:
                    await client_ws.close(code=1011)
                except:
                    pass

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

class ModuleImporter:
    @staticmethod
    def import_function(method_path: str) -> Callable:
        try:
            module, method = method_path.rsplit('.', 1)
            mod = import_module(module)
            return getattr(mod, method)
        except (ImportError, AttributeError) as e:
            raise RequestError(
                f"Failed to import function: {method_path}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def route(
    request_method: Any,
    path: str,
    service_url: str,
    authentication_required: bool = False,
    form_data: bool = False,
    status_code: Optional[int] = None,
    payload_key: Optional[str] = None,
):

    if getattr(request_method, '__name__', '').lower() == 'websocket':
        def websocket_wrapper(func):
            @request_method(path)
            async def inner(websocket: WebSocket):
                print("New websocket connection request")
                try:
                    proxy = SimpleWebSocketProxy(service_url)
                    await proxy.proxy(websocket)
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                    try:
                        await websocket.close(code=1011)
                    except:
                        pass
            return inner
        return websocket_wrapper


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