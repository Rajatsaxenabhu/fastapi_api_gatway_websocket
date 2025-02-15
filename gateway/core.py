import httpx
from fastapi import Request, Response, status,WebSocket ,UploadFile
from typing import List, Optional, Dict, Any, Union, Callable
from importlib import import_module
import base64
from pydantic import BaseModel
import functools
from starlette.datastructures import UploadFile as StarletteUploadFile
from httpx_ws import WebSocketUpgradeError,AsyncWebSocketSession

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


class AllClient:
    def __init__(self):
        self.active_conn:Dict[str,tuple[WebSocket,AsyncWebSocketSession]]

    async def socket_request():
        pass

    async def http_request(
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
                    status_code=e.response.status_code
                )
            except Exception as e:
                raise APIError(
                    status_code=e.response.status_code
                )
            finally:
                await client.aclose()


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
    status_code: int,
    payload_key: str,
    service_url: str,
    authentication_required: bool = False,
    authentication_token_decoder: str = 'auth.decode_access_token',
    service_authorization_checker: str = 'auth.is_admin_user',
    service_header_generator: str = 'auth.generate_request_header',
    response_model: Optional[str] = None,
    response_list: bool = False,
    form_data: bool = False,
):
    if response_model:
        try:
            response_model_class = ModuleImporter.import_function(response_model)
            if response_list:
                response_model_class = List[response_model_class]
        except Exception:
            raise RequestError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        response_model_class = None

    real_link = request_method(
        path,
        response_model=response_model_class,
        status_code=status_code
    )
    client=AllClient()
    def wrapper(func):
        @functools.wraps(func)
        async def inner(request: Union[Request,WebSocket], response: Response, **kwargs):
            if isinstance(request,WebSocket):
                ws_url=f"ws://{service_url.strip('/')}/{path.strip('/')}"
                await client.socket_request(
                    client_ws=request,
                    service_url=ws_url,
                    client_id=none
                )
                pass
            else:
                service_headers = {}

                try:
                    method = request.method.lower()
                    url = f'{service_url}{request.url.path}'
                    payload = await process_payload(payload_key, kwargs, form_data)
                    
                
                    query_params = dict(request.query_params)
                    print("query_params",query_params)
            
                    resp_data, status_code_from_service = await client.http_request(
                        url=url,
                        method=method,
                        data=payload,
                        headers=service_headers,
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

class HTTPClient:
    @staticmethod
    async def make_request(
        url: str,
        method: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> tuple[Any, int]:
        
        headers = headers or {}
        params = params or {}
        
        try:
            client = httpx.AsyncClient()
            response = await client.request(
                method=method.upper(),
                url=url,
                json=data,
                headers=headers,
                params=params,
                timeout=timeout
            )
            try:
                response.raise_for_status()
                return response.json(), response.status_code
            finally:
                await client.aclose()
                
        except httpx.HTTPStatusError as e:
            await client.aclose()
            error_detail = (
                e.response.json().get('detail', str(e))
                if e.response.headers.get('content-type') == 'application/json'
                else str(e)
            )
            raise APIError(
                status_code=e.response.status_code,
                detail=error_detail,
                headers={'WWW-Authenticate': 'Bearer'}
            )
        except httpx.RequestError:
            await client.aclose()
            raise APIError(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Service is unavailable.',
                headers={'WWW-Authenticate': 'Bearer'}
            )
        except Exception:
            await client.aclose()
            raise APIError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Internal server error'
            )

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
                    except Exception as e:
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
            except Exception as e:
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