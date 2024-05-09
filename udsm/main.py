
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas
from .database import get_db, engine
from .routers import nomination, worker, college, department, vote
from .authentication import auth
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins=[
  "*"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nomination.router)
app.include_router(worker.router)
app.include_router(auth.router)
app.include_router(college.router)
app.include_router(department.router)
app.include_router(vote.router)


@app.get("/")
def root():
    return{"message":"Welcome to UDSM Best Worker Selection System API"}
