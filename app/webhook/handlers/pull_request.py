"""pull_request 웹훅 이벤트 핸들러."""
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.github import github_client
from app.services.review_service import review_exists_for_head_sha, update_pr_state

from ._helpers import run_full_review_pipeline

SKIP_REVIEW_LABELS = {"skip-review", "wip"}


async def handle_pull_request(
    action: str,
    payload: dict,
    session: AsyncSession,
) -> None:
    """pull_request 이벤트를 처리한다.

    Args:
        action: 웹훅 액션 (opened, synchronize, closed 등).
        payload: 웹훅 페이로드.
        session: 비동기 DB 세션.
    """
    repo = payload["repository"]
    pr = payload["pull_request"]

    github_repo_id: int = repo["id"]
    pr_number: int = pr["number"]

    if action == "closed":
        new_state = "merged" if pr.get("merged") else "closed"
        logger.info(f"🔒 PR #{pr_number} 상태 업데이트: {new_state}")
        await update_pr_state(session, github_repo_id, pr_number, new_state)
        logger.info(f"✅ PR #{pr_number} 상태 업데이트 완료")

    elif action in ("opened", "synchronize"):
        if action == "opened" and pr.get("draft"):
            logger.info(f"드래프트 PR #{pr_number}, 리뷰 건너뜀")
            return

        installation_id = str(payload["installation"]["id"])
        github_pr_id: int = pr["id"]
        repo_owner: str = repo["owner"]["login"]
        repo_name: str = repo["name"]

        await run_full_review_pipeline(
            session=session,
            installation_id=installation_id,
            github_repo_id=github_repo_id,
            github_pr_id=github_pr_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
        )

    elif action == "ready_for_review":
        head_sha: str = pr["head"]["sha"]
        if await review_exists_for_head_sha(session, github_repo_id, pr_number, head_sha):
            logger.info(f"PR #{pr_number} {head_sha[:7]} 리뷰 이미 존재, 스킵")
            return

        installation_id = str(payload["installation"]["id"])
        github_pr_id = pr["id"]
        repo_owner = repo["owner"]["login"]
        repo_name = repo["name"]

        await run_full_review_pipeline(
            session=session,
            installation_id=installation_id,
            github_repo_id=github_repo_id,
            github_pr_id=github_pr_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            trigger_source="ready_for_review",
        )

    elif action == "labeled":
        label_name = payload["label"]["name"].lower()
        if label_name in SKIP_REVIEW_LABELS:
            installation_id = str(payload["installation"]["id"])
            repo_owner = repo["owner"]["login"]
            repo_name = repo["name"]
            logger.info(f"PR #{pr_number} 스킵 라벨 '{label_name}' 추가, 리뷰 건너뜀")
            await github_client.create_pr_comment(
                installation_id=installation_id,
                repo_owner=repo_owner,
                repo_name=repo_name,
                pull_number=pr_number,
                comment_body=f"`{payload['label']['name']}` 라벨로 인해 코드 리뷰를 건너뜁니다.",
            )

    elif action == "unlabeled":
        label_name = payload["label"]["name"].lower()
        if label_name not in SKIP_REVIEW_LABELS:
            return

        installation_id = str(payload["installation"]["id"])
        repo_owner = repo["owner"]["login"]
        repo_name = repo["name"]

        pr_details = await github_client.get_pr_details(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pr_number,
        )
        current_labels = {label["name"].lower() for label in pr_details.get("labels", [])}
        if current_labels & SKIP_REVIEW_LABELS:
            logger.info(f"PR #{pr_number} 스킵 라벨 여전히 존재 {current_labels & SKIP_REVIEW_LABELS}, 리뷰 건너뜀")
            return

        if pr_details.get("draft"):
            logger.info(f"PR #{pr_number} 드래프트 상태, 리뷰 건너뜀")
            return

        logger.info(f"PR #{pr_number} 스킵 라벨 '{label_name}' 제거, 리뷰 실행")
        await run_full_review_pipeline(
            session=session,
            installation_id=installation_id,
            github_repo_id=github_repo_id,
            github_pr_id=pr["id"],
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            trigger_source="label_removed",
        )

    else:
        logger.debug(f"처리하지 않는 pull_request 액션: {action}")
