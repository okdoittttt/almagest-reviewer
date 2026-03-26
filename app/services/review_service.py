"""리뷰 결과 영속화 서비스."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PullRequest, Repository, Review, ReviewComment
from app.models import PRData


async def upsert_repository(
    session: AsyncSession,
    github_repo_id: int,
    owner: str,
    name: str,
    installation_id: str,
) -> Repository:
    """저장소를 upsert합니다. 이미 존재하면 installation_id를 갱신합니다.

    Args:
        session: 비동기 DB 세션.
        github_repo_id: GitHub에서 발급한 저장소 ID.
        owner: 저장소 소유자 (org 또는 user login).
        name: 저장소 이름.
        installation_id: GitHub App Installation ID.

    Returns:
        저장 또는 갱신된 Repository 인스턴스.
    """
    result = await session.execute(
        select(Repository).where(Repository.github_repo_id == github_repo_id)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        repo = Repository(
            github_repo_id=github_repo_id,
            owner=owner,
            name=name,
            installation_id=installation_id,
        )
        session.add(repo)
        await session.flush()
    else:
        repo.installation_id = installation_id
    return repo


async def upsert_pull_request(
    session: AsyncSession,
    repository_id: int,
    github_pr_id: int,
    pr_data: PRData,
    risk_level: str | None = None,
) -> PullRequest:
    """PR을 upsert합니다. 이미 존재하면 최신 정보로 갱신합니다.

    Args:
        session: 비동기 DB 세션.
        repository_id: 내부 Repository PK.
        github_pr_id: GitHub에서 발급한 PR ID.
        pr_data: PR 데이터 (PRData 인스턴스).
        risk_level: 리스크 수준 (LOW/MEDIUM/HIGH). 옵션.

    Returns:
        저장 또는 갱신된 PullRequest 인스턴스.
    """
    result = await session.execute(
        select(PullRequest).where(
            PullRequest.repository_id == repository_id,
            PullRequest.pr_number == pr_data.pr_number,
        )
    )
    pr = result.scalar_one_or_none()
    if pr is None:
        pr = PullRequest(
            repository_id=repository_id,
            github_pr_id=github_pr_id,
            pr_number=pr_data.pr_number,
            title=pr_data.title,
            author_login=pr_data.author.login,
            head_sha=pr_data.head_sha,
            base_branch=pr_data.base_branch,
            head_branch=pr_data.head_branch,
            state=pr_data.state,
            risk_level=risk_level,
        )
        session.add(pr)
        await session.flush()
    else:
        pr.head_sha = pr_data.head_sha
        pr.state = pr_data.state
        pr.title = pr_data.title
        if risk_level is not None:
            pr.risk_level = risk_level
    return pr


async def save_review(
    session: AsyncSession,
    pull_request_id: int,
    pr_data: PRData,
    review_result: dict,
) -> Review:
    """리뷰 결과를 DB에 저장합니다. 같은 PR이라도 커밋마다 새 row를 생성합니다.

    Args:
        session: 비동기 DB 세션.
        pull_request_id: 내부 PullRequest PK.
        pr_data: PR 데이터.
        review_result: LangGraph run_review() 반환값.

    Returns:
        새로 생성된 Review 인스턴스.
    """
    risk_assessment = review_result.get("risk_assessment") or {}
    review = Review(
        pull_request_id=pull_request_id,
        head_sha=pr_data.head_sha,
        risk_level=risk_assessment.get("level"),
        risk_score=risk_assessment.get("score"),
        pr_intent=review_result.get("pr_intent"),
        risk_assessment=risk_assessment if risk_assessment else None,
        file_reviews=review_result.get("file_reviews", []),
        final_review=review_result.get("final_review"),
        review_decision=review_result.get("review_decision"),
        retry_count=review_result.get("retry_count", 0),
        errors=review_result.get("errors", []),
    )
    session.add(review)
    await session.flush()
    return review


async def save_review_comments(
    session: AsyncSession,
    review_id: int,
    file_reviews: list[dict],
) -> list[ReviewComment]:
    """파일 리뷰에서 개별 코멘트를 추출해 저장합니다.

    file_review dict의 ``issues`` 항목은 ``comment_type="issue"``,
    ``suggestions`` 항목은 ``comment_type="suggestion"`` 으로 저장합니다.

    Args:
        session: 비동기 DB 세션.
        review_id: 내부 Review PK.
        file_reviews: LangGraph file_reviews 리스트.

    Returns:
        저장된 ReviewComment 인스턴스 목록.
    """
    comments: list[ReviewComment] = []
    for file_review in file_reviews:
        filename = file_review.get("filename")
        for issue in file_review.get("issues", []):
            body = issue if isinstance(issue, str) else str(issue)
            comments.append(
                ReviewComment(
                    review_id=review_id,
                    filename=filename,
                    comment_type="issue",
                    body=body,
                )
            )
        for suggestion in file_review.get("suggestions", []):
            body = suggestion if isinstance(suggestion, str) else str(suggestion)
            comments.append(
                ReviewComment(
                    review_id=review_id,
                    filename=filename,
                    comment_type="suggestion",
                    body=body,
                )
            )
    if comments:
        session.add_all(comments)
        await session.flush()
    return comments


async def update_pr_state(
    session: AsyncSession,
    github_repo_id: int,
    pr_number: int,
    state: str,
) -> PullRequest | None:
    """PR 상태를 업데이트합니다.

    Args:
        session: 비동기 DB 세션.
        github_repo_id: GitHub에서 발급한 저장소 ID.
        pr_number: PR 번호.
        state: 새 상태 ("open", "closed", "merged").

    Returns:
        업데이트된 PullRequest 인스턴스. PR이 존재하지 않으면 None.
    """
    repo_result = await session.execute(
        select(Repository).where(Repository.github_repo_id == github_repo_id)
    )
    repo = repo_result.scalar_one_or_none()
    if repo is None:
        return None

    pr_result = await session.execute(
        select(PullRequest).where(
            PullRequest.repository_id == repo.id,
            PullRequest.pr_number == pr_number,
        )
    )
    pr = pr_result.scalar_one_or_none()
    if pr is None:
        return None

    pr.state = state
    return pr


async def persist_review_result(
    session: AsyncSession,
    installation_id: str,
    github_repo_id: int,
    github_pr_id: int,
    pr_data: PRData,
    review_result: dict,
) -> Review:
    """리뷰 결과 전체를 DB에 영속화하는 진입점.

    실행 순서:
    1. repositories upsert
    2. pull_requests upsert
    3. reviews insert
    4. review_comments insert

    Args:
        session: 비동기 DB 세션 (get_db()에서 주입됨).
        installation_id: GitHub App Installation ID.
        github_repo_id: webhook payload["repository"]["id"].
        github_pr_id: webhook payload["pull_request"]["id"].
        pr_data: PR 수집 결과 (PRData 인스턴스).
        review_result: LangGraph run_review() 반환 dict.

    Returns:
        새로 생성된 Review 인스턴스.
    """
    risk_assessment = review_result.get("risk_assessment") or {}
    risk_level = risk_assessment.get("level")

    repo = await upsert_repository(
        session,
        github_repo_id=github_repo_id,
        owner=pr_data.repo_owner,
        name=pr_data.repo_name,
        installation_id=installation_id,
    )

    pr = await upsert_pull_request(
        session,
        repository_id=repo.id,
        github_pr_id=github_pr_id,
        pr_data=pr_data,
        risk_level=risk_level,
    )

    review = await save_review(
        session,
        pull_request_id=pr.id,
        pr_data=pr_data,
        review_result=review_result,
    )

    await save_review_comments(
        session,
        review_id=review.id,
        file_reviews=review_result.get("file_reviews", []),
    )

    return review
