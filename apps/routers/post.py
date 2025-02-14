from typing import Annotated
from fastapi import Response, status, HTTPException, Depends, APIRouter
from psycopg import DatabaseError
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas, oauth2
from ..database import get_db


router = APIRouter(prefix="/posts", tags=["Post"])


# return as list since multiple items can be returned
# @router.get("/", response_model=list[schemas.PostResponse])
@router.get("/", response_model=list[schemas.PostVote])
def get_posts(db: Annotated[Session, Depends(get_db)], limit: int = 10):
    try:
        # posts = db.query(models.Post).limit(limit).all()
        posts = (
            db.query(models.Post, func.count(models.Vote.post_id).label("votes"))
            .join(models.Vote, models.Post.id == models.Vote.post_id, isouter=True)
            .group_by(models.Post.id)
            .all()
        )
        if not posts:
            # will not work since HTTPException is subclass of Exception
            # Exception catches the HTTPException and status gets converted to 500 from 404
            # thus, run HTTPException before exception
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No post found"
            )
        return posts
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database Error: {e}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {e}",
        )


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse
)
def createposts(
    request: schemas.PostCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[schemas.UserOut, Depends(oauth2.get_current_user)],
):
    # do **request to unpack key = value pairs. More useful when you have many fields in body
    new_post = models.Post(
        title=request.title,
        content=request.content,
        published=request.published,
        owner_id=current_user.id,
    )
    try:
        db.add(new_post)
        db.commit()
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
    return new_post


@router.get("/{id}", response_model=schemas.PostVote)
# having {id} in get automatically makes it available to be added to get_posts as a parameter
def get_posts(id: int, db: Session = Depends(get_db)):
    try:
        # must have first() or all() or something of the type to actually return the found values
        # post = db.query(models.Post).filter(models.Post.id == id).first()
        post = (
            db.query(models.Post, func.count(models.Vote.post_id).label("votes"))
            .join(models.Vote, models.Post.id == models.Vote.post_id, isouter=True)
            .filter(models.Post.id == id)
            .group_by(models.Post.id)
            .first()
        )
        if post:
            return post
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Post not found"
            )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database Error: {e}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {e}",
        )


# return 204 on successful deletion
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_posts(
    id: int,
    current_user: Annotated[schemas.UserOut, Depends(oauth2.get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    try:
        # cur.execute("""DELETE FROM POSTS WHERE id = %s returning *""", (id,))
        # deleted_post = cur.fetchone()
        post_to_delete = db.query(models.Post).filter(models.Post.id == id)
        post = post_to_delete.first()
        if post:
            if post.owner_id == current_user.id:
                post_to_delete.delete(synchronize_session="auto")
                db.commit()
                # nothing returned for 204 ever.
                # return 204 response instead
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized Access"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )
    except DatabaseError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Database Error: {e}"
        )
    except HTTPException:
        # No need to raise HTTPException within HTTPException
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {e}",
        )


@router.patch("/{id}", response_model=schemas.PostResponse)
def update_posts(
    id: int,
    post: schemas.PostPatch,
    current_user: Annotated[schemas.UserOut, Depends(oauth2.get_current_user)],
    db: Session = Depends(get_db),
):
    post_dict = post.model_dump(exclude_unset=True)
    try:
        if not post_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid/No fields provided",
            )

        post_query = db.query(models.Post).filter(models.Post.id == id)
        data = post_query.first()
        if data:
            if data.owner_id == current_user.id:
                post_query.update(post_dict, synchronize_session=False)
                db.commit()
                db.refresh(data)
                return data
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized Access"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No data found"
            )
    except DatabaseError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database Error: {e}",
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {e}",
        )
