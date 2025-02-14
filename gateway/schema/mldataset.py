from typing import Literal,List
from fastapi import FastAPI, File, Form, UploadFile,HTTPException
from typing import Annotated,Tuple
from pydantic import model_validator,Field
from pydantic import BaseModel,ConfigDict
from datetime import datetime


class Formdata(BaseModel):
    file_name:str=None
    file:List[UploadFile]

