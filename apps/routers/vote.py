from typing import Annotated
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(prefix="/vote", tags=["Vote"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(
    vote: schemas.Vote,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[schemas.UserOut, Depends(oauth2.get_current_user)],
):
    post = db.query(models.Vote).filter(models.Vote.post_id == vote.post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    query = db.query(models.Vote).filter(
        models.Vote.post_id == vote.post_id, models.Vote.user_id == current_user.id
    )
    vote_post = query.first()
    if vote.dir == 1:
        if vote_post:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User already has voted on this post",
            )
        new_vote = models.Vote(user_id=current_user.id, post_id=vote.post_id)
        db.add(new_vote)
        db.commit()
        return {"message": "Vote added successfully"}
    else:
        if not vote_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vote doesn't exist"
            )
        query.delete(synchronize_session=False)
        db.commit()
        return {"message": "Vote successfully deleted"}
