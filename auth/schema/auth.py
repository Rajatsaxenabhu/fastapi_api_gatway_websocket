from pydantic import BaseModel, EmailStr, Field

class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class RegisterSchema(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)

class DeleteSchema(BaseModel):
    user_id: int

class UpdateSchema(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6)