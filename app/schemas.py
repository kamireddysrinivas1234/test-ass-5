from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo

class CalculationType(str, Enum):
    add = "add"
    sub = "sub"
    mul = "mul"
    div = "div"

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class CalculationBase(BaseModel):
    type: CalculationType
    a: float
    b: float

    @field_validator("b")
    @classmethod
    def no_zero_divisor(cls, v: float, info: ValidationInfo) -> float:
        data = info.data or {}
        calc_type = data.get("type")
        if calc_type == CalculationType.div and v == 0:
            raise ValueError("b cannot be zero for division")
        return v

class CalculationCreate(CalculationBase):
    pass

class CalculationUpdate(BaseModel):
    type: Optional[CalculationType] = None
    a: Optional[float] = None
    b: Optional[float] = None

class CalculationRead(BaseModel):
    id: int
    a: float
    b: float
    type: CalculationType
    result: float
    user_id: Optional[int] = None
    class Config:
        from_attributes = True
