from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.db import get_db
from app.dependencies import get_current_user, require_role
from app.models import Message, User
from app.schemas.message import MessageShow, MessageCreate

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/conversation", response_model=List[MessageShow])
def get_conversation(
        sender_id: Optional[int] = Query(None),
        receiver_id: Optional[int] = Query(None),
        db: Session = Depends(get_db)
):
    query = db.query(Message)

    if sender_id and receiver_id:
        query = query.filter(
            or_(
                and_(Message.sender_id == sender_id, Message.receiver_id == receiver_id),
                and_(Message.sender_id == receiver_id, Message.receiver_id == sender_id)
            )
        )
    elif sender_id:
        query = query.filter(
            or_(Message.sender_id == sender_id, Message.receiver_id == sender_id)
        )
    elif receiver_id:
        query = query.filter(
            or_(Message.sender_id == receiver_id, Message.receiver_id == receiver_id)
        )
    else:
        return []

    return query.order_by(Message.created_at.desc()).all()
