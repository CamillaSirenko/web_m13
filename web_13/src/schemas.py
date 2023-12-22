from pydantic import BaseModel, EmailStr 
from datetime import datetime
from pydantic.fields import Field 


class Token(BaseModel):
    access_token: str
    token_type: str


class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday:datetime
    additional_data: str = None

class ContactCreateUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday:datetime
    additional_data: str = None

class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=16)
    email: str
    password: str = Field(min_length=6, max_length=16)

class UserDb(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str

    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class EmailSchema(BaseModel):
    email: EmailStr

class RequestEmail(BaseModel):
    email: EmailStr