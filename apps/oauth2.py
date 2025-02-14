from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
from typing import Annotated
from . import schemas, models, config
from .database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# Required: SECRET_KEY, ALGORITHM, EXPIRATION_TIME
# run in bash for random secret key: openssl rand -hex 32
SECRET_KEY = config.settings.SECRET_KEY
ALGORITHM = config.settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.settings.ACCESS_TOKEN_EXPIRATION_MINUTES


def create_access_token(data: dict):
    to_encode = data.copy()

    expires = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expires})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> schemas.TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Please Login Again",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, [ALGORITHM])
        print(payload)
        user_id = payload.get("user_id")
        if id is None:
            raise credentials_exception

        # Validation using pydantic schemas
        token_data = schemas.TokenData(id=str(user_id))
    except InvalidTokenError:
        raise credentials_exception
    return token_data


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):

    token_data = verify_access_token(token)

    user = db.query(models.User).filter(models.User.id == token_data.id).first()

    return user
