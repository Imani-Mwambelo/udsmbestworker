from fastapi import Depends
from .models import College, Institute, School, Unit
from .database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import event

# Define event listeners to create Unit instances
def create_unit(db_conn, target):
    
    if isinstance(target, College):
        unit = Unit(unit_name=target.name, unit_type="COLLEGE", unit_id=target.id)
    elif isinstance(target, Institute):
        unit = Unit(unit_name=target.name, unit_type="INSTITUTE", unit_id=target.id)
    elif isinstance(target, School):
        unit = Unit(unit_name=target.name, unit_type="SCHOOL", unit_id=target.id)
    db_conn.add(unit)
    db_conn.commit()

# Attach event listeners
def attach_listeners():
    event.listen(College, 'after_insert', create_unit)
    event.listen(Institute, 'after_insert', create_unit)
    event.listen(School, 'after_insert', create_unit)
