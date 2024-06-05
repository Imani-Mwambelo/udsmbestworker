from pydantic import BaseModel, EmailStr, Field

from udsm.models import College


class CollegeCreate(BaseModel):
    name: str
    dean: str

class CollegeOut(CollegeCreate):
    id:int
    


class DepartmentCreate(BaseModel):
    name: str
    head_of_department: str
    college_id:int

class DepartmentOut(DepartmentCreate):
    college:CollegeOut
    

class Nomination(BaseModel):
    category: str
    nominee_id: int
    weight: int=Field(..., ge=1, le=3)

class Vote(BaseModel):
    category: str
    votee_id: int


    # Data model for a nomination
class Worker(BaseModel):
    email:EmailStr
    password:str
    category: str
    department_id:int


class WorkerOut(BaseModel):
    id:int
    email:EmailStr
    category: str
    department_id:int

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
