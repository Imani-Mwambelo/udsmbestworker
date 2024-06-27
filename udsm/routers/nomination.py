
from fastapi import APIRouter, FastAPI, HTTPException, Depends, status
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from typing import List, Dict
from .. import models, schemas
from sqlalchemy import func
from udsm.authentication import oauth2
from ..database import get_db

router = APIRouter(tags=['Nominations'])


class NominationsStaging:
    def __init__(self):
        self.user_nominations: Dict[str, List[schemas.Nomination]] = {}

    def stage_nomination(self, user_id: str, nomination: schemas.Nomination):
        if user_id not in self.user_nominations:
            self.user_nominations[user_id] = []

        # Count nominations for the same category
        category_count = sum(1 for nom in self.user_nominations[user_id] if nom.category == nomination.category)

        if category_count < 3:
            self.user_nominations[user_id].append(nomination)
        else:
            raise HTTPException(status_code=400, detail="You can only stage three nominations per category")

    def get_staged_nominations(self, user_id: str) -> List[schemas.Nomination]:
        return self.user_nominations.get(user_id, [])

    def clear_staged_nominations(self, user_id: str):
        if user_id in self.user_nominations:
            self.user_nominations[user_id] = []

# Create an instance of the staging class
nominations_staging = NominationsStaging()


def ensure_three_nominations(db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    worker_nominations_count = db.query(models.Nomination).filter(
        models.Nomination.nominator_id == current_user['id']
    ).count()
    if worker_nominations_count != 3:
        raise HTTPException(status_code=400, detail="You must create exactly three nominations")


@router.post("/nominations/", response_model=schemas.Nomination)
def create_nomination(
    nomination: schemas.Nomination,
    db: Session = Depends(get_db),
    current_user: schemas.CurrentUser = Depends(oauth2.get_current_user)
):
    unit = db.query(models.Unit).filter(models.Unit.unit_id == current_user['unit_id']).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unit with id {current_user['unit_id']} does not exist")

    if unit.unit_type == "COLLEGE":
        department = db.query(models.Department).filter(
            models.Department.id == current_user['department_id'],
            models.Department.college_id == current_user['unit_id']
        ).first()

        if not department:
            raise HTTPException(status_code=404, detail="Department not found")

        if not db.query(models.Worker).filter(models.Worker.id == nomination.nominee_id, models.Worker.department_id == department.id).first():
            raise HTTPException(status_code=400, detail="Staff does not belong to the same department")

    nominee = db.query(models.Worker).filter_by(id=nomination.nominee_id, unit_id=current_user['unit_id']).first()
    if not nominee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nominee does not exist in this unit")

    if nominee.category != nomination.category:
        raise HTTPException(status_code=400, detail=f"Nominee is not of {nomination.category} category")

    for staged_nomination in nominations_staging.get_staged_nominations(current_user['id']):
        if staged_nomination.nominee_id == nomination.nominee_id:
            raise HTTPException(status_code=400, detail="You have already nominated this candidate")
        if staged_nomination.weight == nomination.weight and staged_nomination.category==nomination.category:
            raise HTTPException(status_code=400, detail="You can't nominate two candidates with the same weight")

    nominations_staging.stage_nomination(current_user['id'], nomination)
    return nomination


@router.post("/commit-nominations/", response_model=List[schemas.Nomination])
def commit_nominations(
    db: Session = Depends(get_db), 
    current_user: schemas.CurrentUser = Depends(oauth2.get_current_user)
):
    staged_nominations = nominations_staging.get_staged_nominations(current_user['id'])
    
    # Check if the user already has nominations in any of the categories they are trying to nominate
    for staged_nomination in staged_nominations:
        nom_exists = db.query(models.Nomination).filter(
            models.Nomination.nominator_id == current_user['id'],
            models.Nomination.category == staged_nomination.category
        ).first()
        if nom_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"You have already nominated in the {staged_nomination.category} category"
            )
        nominations_staging.clear_staged_nominations(current_user['id'])

    if len(staged_nominations) != 3:
        raise HTTPException(status_code=400, detail="You must stage exactly three nominations")

    try:
        for nomination in staged_nominations:
            db_nomination = models.Nomination(
                **nomination.model_dump(), 
                department_id=current_user['department_id'], 
                nominator_id=current_user['id'],
                unit_id=current_user['unit_id']
            )
            db.add(db_nomination)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while committing nominations")
    nominations_staging.clear_staged_nominations(current_user['id'])
    my_noms = db.query(models.Nomination).filter(models.Nomination.nominator_id == current_user['id']).all()
    return my_noms


#getting all available nominations in a unit
@router.get("/nominations/by-unit/{unit_id}/by-category/{category}")
def all_nominations(unit_id:int, category:str, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nominations = db.query(models.Nomination).filter(models.Nomination.unit_id==unit_id,models.Nomination.category==category).all()
    if not nominations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No nominations found")
    return nominations



#getting all nominations of a worker by using their id
@router.get("/nominations/{nominator_id}")
def my_nominations(nominator_id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nominations = db.query(models.Nomination).filter_by(nominator_id=nominator_id).all()
    if not nominations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No nominations found for this user")
    return nominations


#getting a single nomination of a worker using their id and nomination id
@router.get("/nominations/{nomination_id}")
def my_nomination(nomination_id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nomination = db.query(models.Nomination).filter_by(nominator_id=current_user['id'], id=nomination_id).first()
    if not nomination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nomination not found")
    return nomination




@router.delete("/nominations/{id}")
def delete_nomination(id: int, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nomination = db.query(models.Nomination).filter(models.Nomination.id == id).first()
       
    if not nomination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Nomination with id {id} does not exist")

    if nomination.nominator_id != current_user['id']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this action")
        
    db.delete(nomination)
    db.commit()
    return {"detail": f"Nomination with id {id} was successfully deleted"}


@router.put("/nominations/{id}", response_model=schemas.Nomination)
def update_nomination(id: int, post: schemas.Nomination, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    nomination = db.query(models.Nomination).filter(models.Nomination.id == id).first()
    if not nomination:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Nomination with id {id} does not exist")
    
    if nomination.nominator_id != current_user['id']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform this action")
         
    for key, value in post.model_dump().items():
        setattr(nomination, key, value)
    db.commit()
    return nomination


@router.get("/nom_results/{category}")
def compute_results(category: str, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    try:
        # Delete results only for the specified category and user's unit and department
        db.query(models.Result).filter(models.Result.worker_id.in_(
            db.query(models.Worker.id)
            .filter(
                models.Worker.category == category,
                models.Worker.department_id == current_user['department_id'],
                models.Worker.unit_id == current_user['unit_id']
            )
        )).delete(synchronize_session=False)
        db.commit()
    except OperationalError:
        pass

    unit = db.query(models.Unit).filter(models.Unit.unit_id == current_user['unit_id']).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unit with id {current_user['unit_id']} does not exist")

    # Count total distinct workers who have created nominations in the specified category
    total_workers = db.query(models.Nomination)\
                      .join(models.Worker, models.Nomination.nominator_id == models.Worker.id)\
                      .filter(
                          models.Nomination.category == category,
                          models.Worker.department_id == current_user['department_id'],
                          models.Worker.unit_id == current_user['unit_id']
                      )\
                      .distinct(models.Nomination.nominator_id)\
                      .count()

    if total_workers == 0:
        raise HTTPException(status_code=400, detail="No nominations found for the specified category")

    overall_total_points = 6 * total_workers

    # Calculate results for each worker in the specified category
    worker_results = db.query(models.Nomination.nominee_id, func.sum(models.Nomination.weight).label('total_points'))\
                       .join(models.Worker, models.Nomination.nominee_id == models.Worker.id)\
                       .filter(
                           models.Worker.category == category,
                           models.Worker.department_id == current_user['department_id'],
                           models.Worker.unit_id == current_user['unit_id']
                       )\
                       .group_by(models.Nomination.nominee_id)\
                       .all()

    for worker_id, worker_total_points in worker_results:
        percentage = round((worker_total_points / overall_total_points) * 100, 2) if overall_total_points != 0 else 0
        db_result = models.Result(worker_id=worker_id, percentage=percentage)
        db.add(db_result)

    db.commit()

    # Retrieve results along with worker information for the specified category
    results = db.query(models.Result,models.Worker.id, models.Worker.email, models.Worker.category, models.Worker.name)\
                .join(models.Worker, models.Result.worker_id == models.Worker.id, isouter=True)\
                .filter(
                    models.Worker.category == category,
                    models.Worker.department_id == current_user['department_id'],
                    models.Worker.unit_id == current_user['unit_id']
                )\
                .group_by(models.Result.id, models.Result.worker_id,models.Result,models.Worker.id, models.Worker.email, models.Worker.category, models.Worker.name)\
                .order_by(models.Result.percentage.desc()).limit(3)\
                .all()

    formatted_results = [
        {
            "id":id,
            "name": name,
            "category": worker_category,
            "email": email,
            "percentage": result.percentage,
        }
        for result,id, email, worker_category, name in results
    ]

    return formatted_results







