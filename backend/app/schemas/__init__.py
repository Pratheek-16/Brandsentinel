from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None
    password: str = Field(min_length=8)
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
