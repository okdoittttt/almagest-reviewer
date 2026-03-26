"""위험도와 LLM provider에 따른 diff 길이 한도 계산 모듈.

HIGH 위험도 파일에는 최대 한도를 허용하고,
MEDIUM / LOW로 갈수록 줄여 토큰 비용을 절감합니다.
로컬 LLM(ollama) 사용 시에는 컨텍스트 창 한계를 고려해 전체 상한을 낮춥니다.

설정 키:
    ``DIFF_MAX_CHARS_CLOUD``  — cloud provider(anthropic/google)의 HIGH 기준 상한 (기본 10 000)
    ``DIFF_MAX_CHARS_OLLAMA`` — ollama의 HIGH 기준 상한 (기본 4 000)
"""
from app.config import settings
from app.reviewer.llm import get_current_provider

# 위험도별 적용 비율 (HIGH 상한 대비)
_RISK_RATIOS: dict[str, float] = {
    "HIGH": 1.0,
    "MEDIUM": 0.7,
    "LOW": 0.3,
}


def get_diff_limit(risk_level: str | None = None) -> int:
    """현재 provider와 위험도에 맞는 diff 최대 길이(문자 수)를 반환합니다.

    Args:
        risk_level: ``"LOW"``, ``"MEDIUM"``, ``"HIGH"`` 중 하나.
            None 또는 인식 불가 값이면 ``"MEDIUM"``으로 처리합니다.

    Returns:
        diff를 잘라낼 최대 문자 수.
    """
    provider = get_current_provider()
    high_limit = (
        settings.diff_max_chars_ollama
        if provider == "ollama"
        else settings.diff_max_chars_cloud
    )

    level = (risk_level or "MEDIUM").upper()
    ratio = _RISK_RATIOS.get(level, _RISK_RATIOS["MEDIUM"])

    return max(500, int(high_limit * ratio))  # 최소 500자는 보장
