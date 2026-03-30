"""Prompt injection 방지를 위한 skills 텍스트 살균 유틸리티."""
import re

_MAX_NAME_LEN = 100
_MAX_DESC_LEN = 500
_MAX_CRITERIA_LEN = 2000

# LLM 프롬프트 구조를 무너뜨릴 수 있는 패턴
_INJECTION_PATTERNS = re.compile(
    r"(#{1,6}\s|```|---|\*\*\*|"          # 마크다운 헤더·코드블록·구분선
    r"ignore\s+(all\s+)?(previous|above)|" # 프롬프트 리셋 지시
    r"forget\s+(all\s+)?previous|"
    r"you\s+are\s+now|"
    r"new\s+instructions?:|"
    r"system\s*:)",
    re.IGNORECASE,
)


def sanitize_skill_text(text: str | None, max_len: int) -> str:
    """Skills 이름/설명/기준에서 프롬프트 인젝션 위험 패턴을 제거합니다.

    Args:
        text: 살균할 원본 문자열.
        max_len: 허용 최대 길이.

    Returns:
        살균된 문자열. None이면 빈 문자열 반환.
    """
    if not text:
        return ""
    # 제어 문자 제거
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    # 인젝션 패턴 제거
    text = _INJECTION_PATTERNS.sub("", text)
    # 길이 제한
    return text[:max_len].strip()


def sanitize_skills(repo_skills: list[dict]) -> list[dict]:
    """skills 목록 전체를 살균합니다.

    Args:
        repo_skills: 저장소 Skills 목록.

    Returns:
        name·description·criteria가 살균된 Skills 목록.
    """
    sanitized = []
    for s in repo_skills:
        name = sanitize_skill_text(s.get("name"), _MAX_NAME_LEN)
        description = sanitize_skill_text(s.get("description"), _MAX_DESC_LEN)
        criteria = sanitize_skill_text(s.get("criteria"), _MAX_CRITERIA_LEN)
        if name:  # 이름이 없으면 스킵
            sanitized.append({**s, "name": name, "description": description, "criteria": criteria})
    return sanitized
