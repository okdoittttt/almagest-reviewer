"""
LLM Provider Factory

Anthropic Claude 또는 Google Gemini를 선택하여 사용할 수 있습니다.
"""
from typing import Any
from loguru import logger

from langchain_core.language_models.chat_models import BaseChatModel
from app.config import settings


def get_llm(temperature: float = 0.0, **kwargs: Any) -> BaseChatModel:
    """
    설정에 따라 적절한 LLM을 반환하는 팩토리 함수

    Args:
        temperature: LLM temperature (0.0 = deterministic, 1.0 = creative)
        **kwargs: 추가 LLM 설정

    Returns:
        BaseChatModel 인스턴스 (ChatAnthropic 또는 ChatGoogleGenerativeAI)

    Raises:
        ValueError: 지원하지 않는 provider이거나 API key가 없는 경우
    """
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        return _get_anthropic_llm(temperature, **kwargs)
    elif provider == "google":
        return _get_google_llm(temperature, **kwargs)
    else:
        raise ValueError(
            f"지원하지 않는 LLM provider: {provider}. "
            f"'anthropic' 또는 'google'을 사용하세요."
        )


def _get_anthropic_llm(temperature: float = 0.0, **kwargs: Any) -> BaseChatModel:
    """
    Anthropic Claude LLM 생성

    Args:
        temperature: LLM temperature
        **kwargs: 추가 설정

    Returns:
        ChatAnthropic 인스턴스

    Raises:
        ValueError: API key가 없는 경우
    """
    from langchain_anthropic import ChatAnthropic

    if not settings.anthropic_api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY가 설정되지 않았습니다. "
            ".env 파일에 ANTHROPIC_API_KEY를 추가하세요."
        )

    model = kwargs.pop("model", "claude-3-5-sonnet-20241022")

    logger.debug(f"Anthropic LLM 초기화: {model}, temperature={temperature}")

    return ChatAnthropic(
        model=model,
        api_key=settings.anthropic_api_key,
        temperature=temperature,
        **kwargs
    )


def _get_google_llm(temperature: float = 0.0, **kwargs: Any) -> BaseChatModel:
    """
    Google Gemini LLM 생성

    Args:
        temperature: LLM temperature
        **kwargs: 추가 설정

    Returns:
        ChatGoogleGenerativeAI 인스턴스

    Raises:
        ValueError: API key가 없는 경우
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not settings.google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY가 설정되지 않았습니다. "
            ".env 파일에 GOOGLE_API_KEY를 추가하세요."
        )

    model = kwargs.pop("model", "gemini-2.5-flash")

    logger.debug(f"Google Gemini LLM 초기화: {model}, temperature={temperature}")

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
        **kwargs
    )


def get_current_provider() -> str:
    """
    현재 사용 중인 LLM provider 반환

    Returns:
        provider 이름 (anthropic 또는 google)
    """
    return settings.llm_provider.lower()


def get_available_providers() -> list[str]:
    """
    사용 가능한 LLM provider 목록 반환

    Returns:
        사용 가능한 provider 목록
    """
    available = []

    if settings.anthropic_api_key:
        available.append("anthropic")

    if settings.google_api_key:
        available.append("google")

    return available
