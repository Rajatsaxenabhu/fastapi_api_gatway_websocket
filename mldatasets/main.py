from fastapi import FastAPI,status
from pathlib import Path
from schema.ml_schema import TextSchema
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel
from fastapi import File,UploadFile
from typing import Any
import base64
app=FastAPI()


class FileUploadRequest(BaseModel):
    file_name: str
    files: List[dict]

def re_encode(content: str) -> str:  
    encoded= base64.b64decode(content).decode('utf-8')
    return encoded

def re_encode_img(content: str) -> str:  
    encoded= base64.b64decode(content)
    return encoded



@app.post('/form_files',status_code=status.HTTP_201_CREATED)
async def image_upload_multiple(data:FileUploadRequest):
    try:
        print(data.file_name)
        for i in data.files:
            if i['content_type'].split('/')[0] == 'image':
                print("image file actins started")
            elif i['content_type'].split('/')[0] == 'text':
                print("text file actions started")
                print(re_encode(i['content']))
        return JSONResponse(content={"message":"formdata successful"},status_code=status.HTTP_201_CREATED)
    except Exception as err:
        print("excepr from ml dataet ",str(err))
        return JSONResponse(content={"message":"form data not success"},status_code=status.HTTP_400_BAD_REQUEST)
