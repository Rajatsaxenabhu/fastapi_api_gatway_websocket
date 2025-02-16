from fastapi import FastAPI, status, Request, Response,UploadFile,File,Form
from typing import Tuple,List
from schema.mldataset import Formdata
from conf.conf import settings
from core import route
from schema.auth import UpdateSchema,LoginSchema,DeleteSchema,RegisterSchema
from  typing import Annotated

app = FastAPI()

@route(
    request_method=app.get,
    path='/test',
    status_code=status.HTTP_200_OK,
    service_url=settings.AUTH_SERVICE_URL,
    payload_key="",
    authentication_required=False,
)
async def test(request:Request,response:Response,name:str):
    pass

@route(
    request_method=app.get,
    path='/simple_query',
    status_code=status.HTTP_200_OK,
    service_url=settings.AUTH_SERVICE_URL,
    payload_key=None,
    authentication_required=False,
)
async def page(request:Request,response:Response):
    pass


@route(
    request_method=app.get,
    path='/test_bool',
    status_code=status.HTTP_200_OK,
    service_url=settings.AUTH_SERVICE_URL,
    payload_key=None,
    authentication_required=False,
)
async def test_query(request:Request,response:Response,name:str,values:str):
    pass


@route(
    request_method=app.post,
    path='/login',
    status_code=status.HTTP_201_CREATED,
    service_url=settings.AUTH_SERVICE_URL,
    payload_key="login_data",
    authentication_required=False,
)
async def login(login_data:LoginSchema,request: Request, response: Response):
    pass

@route(
    request_method=app.post,
    path='/register',
    status_code=status.HTTP_201_CREATED,
    service_url=settings.AUTH_SERVICE_URL,
    payload_key="resgister_data",
    authentication_required=False,
)
async def register(resgister_data:RegisterSchema,request: Request, response: Response):
    pass

@route(
    request_method=app.delete,
    path='/delete',
    status_code=status.HTTP_201_CREATED,
    service_url=settings.AUTH_SERVICE_URL,
    payload_key="delete_id",
    authentication_required=False,
)
async def delete(delete_id: DeleteSchema,request: Request, response: Response):
    pass

@route(
    request_method=app.put,
    path='/update',
    status_code=status.HTTP_201_CREATED,
    service_url=settings.AUTH_SERVICE_URL,
    payload_key="update_data",
    authentication_required=False,
)
async def update(update_data:UpdateSchema,request: Request, response: Response):
    pass


@route(
    request_method=app.post,
    path="/form_files",
    status_code=status.HTTP_201_CREATED,
    service_url=settings.MLDATASET_SERVICE_URL,
    payload_key="form_data",
    authentication_required=False,
    form_data=True
)
async def image_upload_multiple(request:Request,response:Response,
                                file_name: Annotated[str, Form()],
                                files: Annotated[List[UploadFile], File()] = []
                                ):
    pass
