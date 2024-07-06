
from typing import Optional
from sqlalchemy import Column, Float, ForeignKey, Integer, String, DateTime, text, Enum, UniqueConstraint
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship, validates




from .database import Base

# class UnitType(Enum):
#     COLLEGE = 'college'
#     INSTITUTE = 'institute'
#     SCHOOL = 'school'

class College(Base):
    __tablename__ = 'colleges'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    departments = relationship('Department', back_populates='college', cascade='all, delete-orphan')

class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    college_id = Column(Integer, ForeignKey('colleges.id'))
    college = relationship('College', back_populates='departments')
    workers = relationship('Worker', back_populates='department')
    

class Institute(Base):
    __tablename__ = 'institutes'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

class School(Base):
    __tablename__ = 'schools'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

class Unit(Base):
    __tablename__ = 'units'
    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String, index=True)
    unit_type = Column(Enum("COLLEGE", "INSTITUTE", "SCHOOL", name="unit_type_enum"), index=True, nullable=False)
    unit_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    workers = relationship('Worker', back_populates='unit')

    __table_args__ = (UniqueConstraint('unit_type', 'unit_id', name='_unit_uc'),)


class Worker(Base):
    __tablename__ = 'workers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, nullable=False)
    password=Column(String, nullable=False)
    category = Column(String, nullable=False)
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    role = Column(String, nullable=False, default="user")
    unit = relationship('Unit', back_populates='workers')
    department = relationship('Department', back_populates='workers')
    
class NominationPeriod(Base):
    __tablename__ = 'nomination_periods'
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    created_at= Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class VotingPeriod(Base):
    __tablename__ = 'voting_periods'
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    created_at= Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class NominationResultReleasePeriod(Base):
    __tablename__ = 'nom_result_release_periods'
    id = Column(Integer, primary_key=True, index=True)
    release_time = Column(DateTime(timezone=True), nullable=False)
    created_at= Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class ResultReleasePeriod(Base):
    __tablename__ = 'result_release_periods'
    id = Column(Integer, primary_key=True, index=True)
    release_time = Column(DateTime(timezone=True), nullable=False)
    created_at= Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
   


#sqlalchemy will check if a table exists in the db if yes it will not create them otherwise it will create them but it can not modify existing tables
class Nomination(Base):
    __tablename__ = "nominations"

    id = Column(Integer, primary_key=True)
    nominator_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    nominee_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    created_at= Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    department_id = Column(Integer, ForeignKey("departments.id"),  nullable=True)
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=False)

    

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True)
    voter_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    votee_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    created_at= Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=False)


    

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    percentage = Column(Float, server_default="0")

    #owner = relationship("User")

class VoteResult(Base):
    __tablename__ = "voteresults"

    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    percentage = Column(Float, server_default="0")






