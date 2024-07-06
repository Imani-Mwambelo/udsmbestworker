from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, field_serializer

from udsm.models import College

class UnitCreate(BaseModel):
    name: str
    

class UnitOut(UnitCreate):
    id: int
    
class CollegeCreate(BaseModel):
    name: str
    
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
    id:int

    class Config:
        orm_mode: True

class CollegeOut(CollegeCreate):
    id: int

    class Config:
        orm_mode: True





class NominationPeriodBase(BaseModel):
    start_time: str = Field(..., example="2024-06-27 00:00:54")
    end_time: str = Field(..., example="2024-06-29 01:50:54")

    @field_validator('start_time', 'end_time')
    def validate_datetime(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("Datetime format must be 'YYYY-MM-DD HH:MM:SS'")
        return v


class NominationPeriodCreate(NominationPeriodBase):
    pass

class NominationPeriodOut(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime


    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            start_time=obj.start_time.isoformat(),
            end_time=obj.end_time.isoformat()
        )
    class Config:
        orm_mode: True

class VotingPeriodBase(BaseModel):
    start_time: str = Field(..., example="2024-06-27 00:00:54")
    end_time: str = Field(..., example="2024-06-29 01:50:54")

    @field_validator('start_time', 'end_time')
    def validate_datetime(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("Datetime format must be 'YYYY-MM-DD HH:MM:SS'")
        return v
    
class VotingPeriodCreate(VotingPeriodBase):
    pass

class VotingPeriodOut(NominationPeriodOut):
    pass

class ResultReleasePeriodBase(BaseModel):
    release_time: str = Field(..., example="2024-06-27 00:00:54")

    @field_validator('release_time')
    def validate_datetime(cls, v):
        if isinstance(v, datetime):
            v = v.strftime("%Y-%m-%d %H:%M:%S")  # Convert datetime to string
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("Datetime format must be 'YYYY-MM-DD HH:MM:SS'")
        return v
    

class ResultReleasePeriodCreate(ResultReleasePeriodBase):
    pass

class ResultReleasePeriodOut(ResultReleasePeriodBase):
    id: int
    release_time: datetime

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            release_time=obj.release_time.isoformat(),
        )
    class Config:
        orm_mode: True  

class Nomination(BaseModel):
    category: str
    nominee_id: int
    weight: int=Field(..., ge=1, le=3)

class Vote(BaseModel):
    category: str
    votee_id: int

class VoteOut(Vote):
    voter_id: int
    id:int


    # Data model for a nomination
class Worker(BaseModel):
    name:str
    email:EmailStr
    password:str
    category: str
    role: Optional[str]="user"
    unit_id:int
    department_id:Optional[int]


class WorkerOut(BaseModel):
    id:int
    role:str
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
    role:str

class Result(BaseModel):
    worker_id:int
    percentage:float
    

class CurrentUser(BaseModel):
    id:int
    role:str
    category:str
    department_id: int
    unit_id:int
