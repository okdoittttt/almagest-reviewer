"""GitHub 웹훅 이벤트 디스패처."""
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .handlers import handle_pull_request


async def dispatch_event(
    event: str,
    action: str,
    payload: dict,
    session: AsyncSession,
) -> None:
    """이벤트 타입에 따라 적절한 핸들러로 라우팅한다.

    Args:
        event: x-github-event 헤더 값.
        action: payload["action"] 값.
        payload: 웹훅 페이로드.
        session: 비동기 DB 세션.
    """
    if event == "pull_request":
        await handle_pull_request(action, payload, session)
    else:
        logger.debug(f"처리하지 않는 이벤트: {event}")
