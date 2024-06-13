from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from udsm.models import College

class UnitCreate(BaseModel):
    name: str
    

class UnitOut(UnitCreate):
    id: int
    
class CollegeCreate(BaseModel):
    name: str
    

class CollegeOut(CollegeCreate):
    id: int
    
class InstituteCreate(BaseModel):
    name: str


class InstituteOut(InstituteCreate):
    id: int
class SchoolCreate(BaseModel):
    name: str
    

class SchoolOut(SchoolCreate):
    id: int
        

class DepartmentCreate(BaseModel):
    name: str
    college_id:int

class DepartmentOut(DepartmentCreate):
    id:str
    college:CollegeOut

    class Config:
        orm_mode: True

    

class Nomination(BaseModel):
    category: str
    nominee_id: int
    weight: int=Field(..., ge=1, le=3)

class Vote(BaseModel):
    category: str
    votee_id: int


    # Data model for a nomination
class Worker(BaseModel):
    name:str
    email:EmailStr
    password:str
    category: str
    unit_id:int
    department_id:Optional[int]


class WorkerOut(BaseModel):
    id:int
    email:EmailStr
    name:str
    category: str
    unit_id:int
    department_id: Optional[int] = None

    class Config:
        orm_mode: True


class UserLogin(BaseModel):
    email:EmailStr
    password:str

class Token(BaseModel):
    access_token:str
    token_type:str

class Result(BaseModel):
    worker_id:int
    percentage:float
    

class CurrentUser(BaseModel):
    id:int
    category:str
    department_id: int
