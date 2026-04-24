from pydantic import BaseModel, EmailStr
from typing import Optional

# What we need from the user to create an account
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "citizen" # Default role; can be 'police'

# What the API sends back after a successful login
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: Optional[str] = None
    access_token: str