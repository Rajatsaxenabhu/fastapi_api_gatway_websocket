from typing import Literal,List
from fastapi import FastAPI, File, Form, UploadFile,HTTPException
from typing import Annotated
from pydantic import model_validator,Field
from pydantic import BaseModel,ConfigDict
from datetime import datetime
import base64


class TextSchema(BaseModel):
    content: str

    @classmethod
    def convert_to_text(self, content):
        pass



