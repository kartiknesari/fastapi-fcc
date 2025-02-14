from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from ..database import get_db
from .. import schemas, models, utils, oauth2

router = APIRouter(prefix="/auth", tags=["Authentication"])


# OAuth2PasswordRequestForm makes the data as a form so require form-data in postman instead of body
@router.post("/login", response_model=schemas.Token)
def login(
    request: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        user = (
            db.query(models.User).filter(models.User.email == request.username).first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Credentials",
            )
        if not utils.verify(request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Credentials",
            )

        # create and return token
        # Pydantic validates models on initialization so doing a blank schemas.Token() won't work
        token = schemas.Token(
            access_token=oauth2.create_access_token(data={"user_id": user.id}),
            token_type="bearer",
        )
        return token
    except HTTPException:
        raise
    except Exception as e:
        print({e})
        HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
