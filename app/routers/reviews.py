"""Review / ReviewComment 조회 및 업데이트 API."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models.review import Review
from app.database.models.review_comment import ReviewComment
from app.schemas.review import ReviewCommentOut, ReviewDetail

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/{review_id}", response_model=ReviewDetail)
async def get_review(review_id: int, session: AsyncSession = Depends(get_db)) -> ReviewDetail:
    review = await session.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewDetail.model_validate(review)


@router.get("/{review_id}/comments", response_model=list[ReviewCommentOut])
async def list_review_comments(review_id: int, session: AsyncSession = Depends(get_db)) -> list[ReviewCommentOut]:
    review = await session.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    rows = await session.execute(
        select(ReviewComment)
        .where(ReviewComment.review_id == review_id)
        .order_by(ReviewComment.filename, ReviewComment.id)
    )
    return [ReviewCommentOut.model_validate(c) for c in rows.scalars()]


class AddressedUpdate(BaseModel):
    is_addressed: bool


@router.patch("/{review_id}/comments/{comment_id}", response_model=ReviewCommentOut)
async def update_comment_addressed(
    review_id: int,
    comment_id: int,
    body: AddressedUpdate,
    session: AsyncSession = Depends(get_db),
) -> ReviewCommentOut:
    comment = await session.get(ReviewComment, comment_id)
    if comment is None or comment.review_id != review_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.is_addressed = body.is_addressed
    comment.addressed_at = datetime.now(timezone.utc) if body.is_addressed else None
    await session.flush()
    return ReviewCommentOut.model_validate(comment)
