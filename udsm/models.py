
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, text, DECIMAL
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship

from .database import Base



class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    dean = Column(String)
    departments = relationship("Department", back_populates="college")

  

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    head_of_department = Column(String)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    college = relationship("College", back_populates="departments")
    workers = relationship("Worker", back_populates="department")
    nominations = relationship("Nomination", back_populates="department")




class Worker(Base):
  __tablename__ = "workers"

  id = Column(Integer, primary_key=True)
  email = Column(String, unique=True, nullable=False)
  password=Column(String, nullable=False)
  category = Column(String, nullable=False)
  department_id = Column(Integer, ForeignKey("departments.id"))
  department = relationship("Department", back_populates="workers")
  created_at= Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


#items = relationship("Item", back_populates="owner")

#sqlalchemy will check if a table called posts&users exists in the db if yes it will not create them otherwise it will create them but it can not modify existing tables
class Nomination(Base):
    __tablename__ = "nominations"

    id = Column(Integer, primary_key=True)
    nominator_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    nominee_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    created_at= Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    department_id = Column(Integer, ForeignKey("departments.id"))
    department = relationship("Department", back_populates="nominations")

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True)
    voter_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    votee_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    created_at= Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    department_id = Column(Integer, ForeignKey("departments.id"))


    

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



# class Vote(Base):
#    __tablename__="votes"
#    user_id=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
#    post_id=Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)



