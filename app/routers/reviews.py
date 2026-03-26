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
from app.services.review_service import create_comment_reply

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/{review_id}", response_model=ReviewDetail)
async def get_review(review_id: int, session: AsyncSession = Depends(get_db)) -> ReviewDetail:
    """단일 리뷰의 상세 정보를 반환한다.

    Args:
        review_id: Review 내부 PK.
        session: 비동기 DB 세션.

    Returns:
        ReviewDetail 스키마.

    Raises:
        HTTPException: review_id에 해당하는 리뷰가 없으면 404.
    """
    review = await session.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewDetail.model_validate(review)


@router.get("/{review_id}/comments", response_model=list[ReviewCommentOut])
async def list_review_comments(review_id: int, session: AsyncSession = Depends(get_db)) -> list[ReviewCommentOut]:
    """특정 리뷰에 속한 코멘트 목록을 반환한다.

    Args:
        review_id: Review 내부 PK.
        session: 비동기 DB 세션.

    Returns:
        파일명 · id 순으로 정렬된 ReviewCommentOut 목록.

    Raises:
        HTTPException: review_id에 해당하는 리뷰가 없으면 404.
    """
    review = await session.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    rows = await session.execute(
        select(ReviewComment)
        .where(ReviewComment.review_id == review_id)
        .order_by(ReviewComment.filename, ReviewComment.id)
    )
    return [ReviewCommentOut.model_validate(c) for c in rows.scalars()]


class ReplyCreate(BaseModel):
    body: str


class AddressedUpdate(BaseModel):
    is_addressed: bool


@router.post("/{review_id}/comments/{comment_id}/replies", response_model=ReviewCommentOut)
async def post_comment_reply(
    review_id: int,
    comment_id: int,
    body: ReplyCreate,
    session: AsyncSession = Depends(get_db),
) -> ReviewCommentOut:
    """리뷰 코멘트에 답글을 작성합니다.

    Args:
        review_id: 답글이 속할 Review PK.
        comment_id: 답글 대상 ReviewComment PK.
        body: 답글 내용.
        session: 비동기 DB 세션.

    Returns:
        저장된 답글 ReviewComment.

    Raises:
        HTTPException: comment_id가 해당 review에 속하지 않으면 404.
    """
    try:
        reply = await create_comment_reply(session, review_id, comment_id, body.body)
    except ValueError:
        raise HTTPException(status_code=404, detail="Comment not found")
    return ReviewCommentOut.model_validate(reply)


@router.patch("/{review_id}/comments/{comment_id}", response_model=ReviewCommentOut)
async def update_comment_addressed(
    review_id: int,
    comment_id: int,
    body: AddressedUpdate,
    session: AsyncSession = Depends(get_db),
) -> ReviewCommentOut:
    """코멘트의 처리 완료 여부를 업데이트한다.

    Args:
        review_id: Review 내부 PK.
        comment_id: ReviewComment 내부 PK.
        body: is_addressed 값.
        session: 비동기 DB 세션.

    Returns:
        업데이트된 ReviewCommentOut.

    Raises:
        HTTPException: comment_id가 없거나 해당 review에 속하지 않으면 404.
    """
    comment = await session.get(ReviewComment, comment_id)
    if comment is None or comment.review_id != review_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.is_addressed = body.is_addressed
    comment.addressed_at = datetime.now(timezone.utc) if body.is_addressed else None
    await session.flush()
    await session.refresh(comment)
    return ReviewCommentOut.model_validate(comment)
