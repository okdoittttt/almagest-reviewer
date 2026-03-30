"""스킬 라우팅 — 파일 경로에 적용할 스킬을 패턴 매칭으로 결정합니다."""
from pathlib import PurePosixPath


def _matches_pattern(filename: str, pattern: str) -> bool:
    """파일 경로가 glob 패턴에 매칭되는지 확인합니다.

    PurePosixPath.match()를 사용하며, ``**`` 패턴이 루트 레벨 파일에도
    매칭될 수 있도록 가상 루트 컴포넌트를 추가해 재시도합니다.

    Args:
        filename: 리뷰 대상 파일 경로 (예: ``migrations/0001.py``).
        pattern: glob 패턴 (예: ``**/migrations/**``).

    Returns:
        매칭 여부.
    """
    path = PurePosixPath(filename)
    if path.match(pattern):
        return True
    # ** 패턴은 경로에 상위 디렉토리가 없으면 매칭 실패하는 경우가 있음
    # 가상 루트를 추가해 재시도 (예: "test_foo.py" → "_root/test_foo.py")
    if "**" in pattern:
        return PurePosixPath("_root/" + filename).match(pattern)
    return False


def get_applicable_skills(filename: str, skills: list[dict]) -> list[dict]:
    """파일 경로에 적용할 스킬 목록을 반환합니다.

    file_patterns가 비어있는 스킬은 모든 파일에 적용됩니다.
    file_patterns가 있는 스킬은 패턴 중 하나라도 매칭될 때만 적용됩니다.

    Args:
        filename: 리뷰 대상 파일 경로 (예: ``app/routers/users.py``).
        skills: 저장소에 등록된 활성 스킬 목록.

    Returns:
        이 파일에 적용할 스킬 목록.
    """
    result = []
    for skill in skills:
        patterns = skill.get("file_patterns") or []
        if not patterns:
            result.append(skill)
        elif any(_matches_pattern(filename, p) for p in patterns):
            result.append(skill)
    return result
