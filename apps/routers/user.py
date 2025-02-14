from typing import Annotated
from fastapi import status, HTTPException, Depends, APIRouter
from psycopg import DatabaseError
from sqlalchemy.orm import Session
from .. import models, schemas, utils
from ..database import get_db

router = APIRouter(prefix="/users", tags=["User"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_users(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # password hash
    user.password = utils.hash(user.password)

    try:
        new_user = models.User(**user.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except DatabaseError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database Error: {e}",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {e}",
        )


@router.get("/{id}", response_model=schemas.UserOut)
def get_users(id: int, db: Annotated[Session, Depends(get_db)]):
    try:
        user = db.query(models.User).filter(models.User.id == id).first()
        print(f"User: {user}")
        if user is None:
            # will not work since HTTPException is subclass of Exception
            # Exception catches the HTTPException and status gets converted to 500 from 404
            # thus, run HTTPException before exception
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not Found",
            )

        return user
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e}",
        )
