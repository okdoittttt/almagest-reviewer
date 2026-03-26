"""Review / ReviewComment 조회 및 업데이트 API."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.models.pull_request import PullRequest
from app.database.models.repository import Repository
from app.database.models.review import Review
from app.database.models.review_comment import ReviewComment
from app.github import github_client
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


class ReplyCreate(BaseModel):
    body: str


class AddressedUpdate(BaseModel):
    is_addressed: bool


@router.post("/{review_id}/comments/{comment_id}/replies", response_model=ReviewCommentOut)
async def create_comment_reply(
    review_id: int,
    comment_id: int,
    body: ReplyCreate,
    session: AsyncSession = Depends(get_db),
) -> ReviewCommentOut:
    parent = await session.get(ReviewComment, comment_id)
    if parent is None or parent.review_id != review_id:
        raise HTTPException(status_code=404, detail="Comment not found")

    review = await session.get(Review, review_id)
    pr = await session.get(PullRequest, review.pull_request_id)
    repo = await session.get(Repository, pr.repository_id)

    reply = ReviewComment(
        review_id=review_id,
        parent_id=comment_id,
        filename=parent.filename,
        comment_type="reply",
        body=body.body,
    )
    session.add(reply)
    await session.flush()
    await session.refresh(reply)

    try:
        await github_client.create_pr_review_reply(
            installation_id=repo.installation_id,
            repo_owner=repo.owner,
            repo_name=repo.name,
            pull_number=pr.pr_number,
            body=body.body,
        )
    except Exception:
        pass  # GitHub 게시 실패해도 로컬 저장은 유지

    return ReviewCommentOut.model_validate(reply)


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
    await session.refresh(comment)
    return ReviewCommentOut.model_validate(comment)
