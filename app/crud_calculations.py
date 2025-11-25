from typing import List, Optional
from sqlalchemy.orm import Session
from . import models, schemas
from .schemas import CalculationType
from .calculation_factory import get_operation

def browse_calculations(db: Session, user_id: Optional[int] = None) -> List[models.Calculation]:
    query = db.query(models.Calculation)
    if user_id is not None:
        query = query.filter(models.Calculation.user_id == user_id)
    return query.all()

def get_calculation(db: Session, calc_id: int) -> Optional[models.Calculation]:
    return db.query(models.Calculation).filter(models.Calculation.id == calc_id).first()

def create_calculation(db: Session, calc_in: schemas.CalculationCreate, user_id: Optional[int] = None) -> models.Calculation:
    op = get_operation(calc_in.type, calc_in.a, calc_in.b)
    result = op.compute()
    db_calc = models.Calculation(
        a=calc_in.a,
        b=calc_in.b,
        type=calc_in.type.value,
        result=result,
        user_id=user_id,
    )
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc

def update_calculation(db: Session, calc: models.Calculation, update: schemas.CalculationUpdate) -> models.Calculation:
    if update.a is not None:
        calc.a = update.a
    if update.b is not None:
        calc.b = update.b
    if update.type is not None:
        calc.type = update.type.value
    op = get_operation(CalculationType(calc.type), calc.a, calc.b)
    calc.result = op.compute()
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc

def delete_calculation(db: Session, calc: models.Calculation) -> None:
    db.delete(calc)
    db.commit()
