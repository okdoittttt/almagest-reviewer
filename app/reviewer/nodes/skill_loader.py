"""Skill Loader Node — 저장소별 커스텀 리뷰 기준을 DB에서 로드합니다."""
from loguru import logger
from sqlalchemy import select

from app.database import async_session_factory
from app.database.models.repository import Repository
from app.database.models.skill import Skill
from app.reviewer.state import ReviewState


async def load_repo_skills(state: ReviewState) -> dict:
    """리뷰 시작 전 저장소에 등록된 활성 Skills를 로드하는 노드.

    repo_owner / repo_name 으로 저장소를 조회한 뒤, 해당 저장소의
    is_enabled=True인 Skill 목록을 ``repo_skills`` 필드에 저장합니다.
    저장소가 없거나 Skills가 없는 경우 빈 리스트로 설정합니다.

    Args:
        state: 현재 리뷰 상태.

    Returns:
        ``repo_skills`` 키를 포함하는 상태 업데이트 딕셔너리.
    """
    repo_owner = state["repo_owner"]
    repo_name = state["repo_name"]

    try:
        async with async_session_factory() as session:
            repo_result = await session.execute(
                select(Repository).where(
                    Repository.owner == repo_owner,
                    Repository.name == repo_name,
                )
            )
            repo = repo_result.scalar_one_or_none()

            if repo is None:
                logger.info(f"📦 저장소 미등록 ({repo_owner}/{repo_name}) — Skills 없음")
                return {"repo_skills": [], "repo_system_prompt": None}

            skills_result = await session.execute(
                select(Skill).where(
                    Skill.repository_id == repo.id,
                    Skill.is_enabled.is_(True),
                )
            )
            skills = skills_result.scalars().all()

            repo_skills = [
                {"name": s.name, "description": s.description, "criteria": s.criteria}
                for s in skills
            ]

            if repo_skills:
                logger.info(f"🎯 Skills 로드 완료: {len(repo_skills)}개 ({repo_owner}/{repo_name})")
            else:
                logger.info(f"🎯 등록된 Skills 없음 ({repo_owner}/{repo_name})")

            if repo.system_prompt:
                logger.info(f"📝 system_prompt 로드 완료 ({repo_owner}/{repo_name})")

            return {"repo_skills": repo_skills, "repo_system_prompt": repo.system_prompt}

    except Exception as e:
        logger.warning(f"⚠️ Skills 로드 실패 (리뷰는 계속 진행): {e}")
        return {"repo_skills": [], "repo_system_prompt": None}
