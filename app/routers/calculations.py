from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, crud_calculations, models
from ..dependencies import get_db, get_current_user

router = APIRouter(prefix="/calculations", tags=["calculations"])

@router.get("/", response_model=List[schemas.CalculationRead])
def browse_calculations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud_calculations.browse_calculations(db, user_id=current_user.id)

@router.post("/", response_model=schemas.CalculationRead, status_code=status.HTTP_201_CREATED)
def add_calculation(
    calc_in: schemas.CalculationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud_calculations.create_calculation(db, calc_in, user_id=current_user.id)

@router.get("/{calc_id}", response_model=schemas.CalculationRead)
def read_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    calc = crud_calculations.get_calculation(db, calc_id)
    if not calc or calc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc

@router.put("/{calc_id}", response_model=schemas.CalculationRead)
@router.patch("/{calc_id}", response_model=schemas.CalculationRead)
def edit_calculation(
    calc_id: int,
    update: schemas.CalculationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    calc = crud_calculations.get_calculation(db, calc_id)
    if not calc or calc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return crud_calculations.update_calculation(db, calc, update)

@router.delete("/{calc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    calc = crud_calculations.get_calculation(db, calc_id)
    if not calc or calc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Calculation not found")
    crud_calculations.delete_calculation(db, calc)
    return None
