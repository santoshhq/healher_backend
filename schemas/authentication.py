from pydantic import BaseModel,EmailStr, computed_field,Field
from typing import Optional
from uuid import uuid4

class signup(BaseModel):
    userId: Optional[str] = None
    name:str=Field(...,)
    email_id:EmailStr=Field(...,)
    mobile_number:str=Field(...,)
    password:str=Field(...,)


class signin(BaseModel):
    email_id:EmailStr=Field(..., description="User email")
    password:str=Field(..., description="User password")


class forgot_password(BaseModel):
    email_id:EmailStr=Field(..., description="User email for password reset")


class reset_password(BaseModel):
    email_id:EmailStr=Field(..., description="User email")
    otp:str=Field(..., description="OTP received in email")
    new_password:str=Field(..., description="New password")