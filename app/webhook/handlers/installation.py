"""GitHub App installation 이벤트 핸들러."""
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.review_service import deactivate_repositories, upsert_repository


async def handle_installation(
    action: str,
    payload: dict,
    session: AsyncSession,
) -> None:
    """installation 이벤트를 처리한다.

    action=created 시 payload["repositories"]에 담긴 레포를 DB에 upsert하고,
    action=deleted 시 해당 레포들을 비활성화한다.

    Args:
        action: payload["action"] 값 ("created" | "deleted" | 기타).
        payload: 웹훅 페이로드.
        session: 비동기 DB 세션.
    """
    installation_id = str(payload["installation"]["id"])
    repositories = payload.get("repositories", [])

    if action == "created":
        if not repositories:
            logger.warning(
                f"installation.created: installation_id={installation_id} — "
                "repositories 리스트가 비어 있음. 첫 PR 웹훅에서 자동 등록됨."
            )
            return
        for repo in repositories:
            owner, name = repo["full_name"].split("/", 1)
            await upsert_repository(
                session,
                github_repo_id=repo["id"],
                owner=owner,
                name=name,
                installation_id=installation_id,
            )
            logger.info(f"레포 등록: {repo['full_name']} (installation={installation_id})")

    elif action == "deleted":
        github_repo_ids = [repo["id"] for repo in repositories]
        deactivated = await deactivate_repositories(session, github_repo_ids)
        logger.info(
            f"installation.deleted: installation_id={installation_id} — "
            f"{deactivated}개 레포 비활성화"
        )

    else:
        logger.debug(f"처리하지 않는 installation action: {action}")


async def handle_installation_repositories(
    action: str,
    payload: dict,
    session: AsyncSession,
) -> None:
    """installation_repositories 이벤트를 처리한다.

    action=added 시 추가된 레포를 DB에 upsert하고,
    action=removed 시 제거된 레포를 비활성화한다.

    Args:
        action: payload["action"] 값 ("added" | "removed" | 기타).
        payload: 웹훅 페이로드.
        session: 비동기 DB 세션.
    """
    installation_id = str(payload["installation"]["id"])

    if action == "added":
        for repo in payload.get("repositories_added", []):
            owner, name = repo["full_name"].split("/", 1)
            await upsert_repository(
                session,
                github_repo_id=repo["id"],
                owner=owner,
                name=name,
                installation_id=installation_id,
            )
            logger.info(f"레포 추가 등록: {repo['full_name']} (installation={installation_id})")

    elif action == "removed":
        github_repo_ids = [repo["id"] for repo in payload.get("repositories_removed", [])]
        deactivated = await deactivate_repositories(session, github_repo_ids)
        logger.info(
            f"installation_repositories.removed: {deactivated}개 레포 비활성화 "
            f"(installation={installation_id})"
        )

    else:
        logger.debug(f"처리하지 않는 installation_repositories action: {action}")
