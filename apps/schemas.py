from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, Field


# TOKEN
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):  # Used for embedding data to create access token
    id: str | None = None


# USER
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


# POSTS
class PostBase(BaseModel):
    title: str
    content: str
    # default value allocated, creates optional field
    published: bool = True


class PostCreate(PostBase):
    pass


class PostPatch(BaseModel):
    title: Optional[str] = Field(default=None)
    content: Optional[str] = Field(default=None)
    published: Optional[bool] = Field(default=True)


class PostResponse(PostBase):
    id: int
    created_at: datetime
    owner_id: int
    owner: UserOut

    # from_attributes (orm_mode earlier) used for telling fastapi to consider the sqlalchemy model as a dictionary
    class Config:
        from_attributes = True


class PostVote(BaseModel):
    Post: PostResponse
    votes: int

    class Config:
        from_attributes = True


class Vote(BaseModel):
    post_id: int
    dir: Annotated[int, Field(le=1)]
