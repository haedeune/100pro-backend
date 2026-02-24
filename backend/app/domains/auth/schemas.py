from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    provider: str

    class Config:
        from_attributes = True

class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class KakaoLogin(BaseModel):
    code: str  # Kakao Authorization Code

class LinkAccountRequest(BaseModel):
    temp_token: str
    password: str
