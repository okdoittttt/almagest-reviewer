"""
LLM Provider Factory

Anthropic Claude 또는 Google Gemini를 선택하여 사용할 수 있습니다.
"""
from typing import Any
from loguru import logger

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from app.config import settings


def get_llm(temperature: float = 0.0, **kwargs: Any) -> BaseChatModel:
    """설정에 따라 적절한 LLM을 반환하는 팩토리 함수.

    Args:
        temperature: LLM temperature. 0.0은 결정론적, 1.0은 창의적 응답을 생성합니다.
        **kwargs: 추가 LLM 설정.

    Returns:
        설정된 provider에 맞는 BaseChatModel 인스턴스.

    Raises:
        ValueError: 지원하지 않는 provider이거나 API key가 없는 경우.
    """
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        return _get_anthropic_llm(temperature, **kwargs)
    elif provider == "google":
        return _get_google_llm(temperature, **kwargs)
    elif provider == "ollama":
        return _get_ollama_llm(temperature, **kwargs)
    else:
        raise ValueError(
            f"지원하지 않는 LLM provider: {provider}. "
            f"'anthropic', 'google', 'ollama'을 사용하세요."
        )


def _get_anthropic_llm(temperature: float = 0.0, **kwargs: Any) -> BaseChatModel:
    """Anthropic Claude LLM을 생성합니다.

    Args:
        temperature: LLM temperature.
        **kwargs: 추가 설정.

    Returns:
        ChatAnthropic 인스턴스.

    Raises:
        ValueError: ANTHROPIC_API_KEY가 설정되지 않은 경우.
    """
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
    """Google Gemini LLM을 생성합니다.

    Args:
        temperature: LLM temperature.
        **kwargs: 추가 설정.

    Returns:
        ChatGoogleGenerativeAI 인스턴스.

    Raises:
        ValueError: GOOGLE_API_KEY가 설정되지 않은 경우.
    """
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


def _get_ollama_llm(temperature: float = 0.0, **kwargs: Any) -> BaseChatModel:
    """Ollama 로컬 LLM 생성.

    Args:
        temperature: LLM temperature.
        **kwargs: 추가 설정.

    Returns:
        ChatOllama 인스턴스.

    Raises:
        ValueError: OLLAMA_BASE_URL이 설정되지 않은 경우.
    """
    if not settings.ollama_base_url:
        raise ValueError(
            "OLLAMA_BASE_URL이 설정되지 않았습니다. "
            ".env 파일에 OLLAMA_BASE_URL을 추가하세요."
        )

    model = kwargs.pop("model", settings.ollama_model)

    logger.debug(f"Ollama LLM 초기화: {model}, base_url={settings.ollama_base_url}, temperature={temperature}")

    return ChatOllama(
        model=model,
        base_url=settings.ollama_base_url,
        temperature=temperature,
        **kwargs
    )


def get_current_provider() -> str:
    """현재 사용 중인 LLM provider 반환.

    Returns:
        provider 이름 (``"anthropic"``, ``"google"``, ``"ollama"`` 중 하나).
    """
    return settings.llm_provider.lower()


def get_available_providers() -> list[str]:
    """사용 가능한 LLM provider 목록을 반환합니다.

    Returns:
        사용 가능한 provider 이름 목록. Ollama는 항상 포함됩니다.
    """
    available = []

    if settings.anthropic_api_key:
        available.append("anthropic")

    if settings.google_api_key:
        available.append("google")

    # Ollama는 항상 연결 가능 여부와 무관하게 목록에 포함
    available.append("ollama")

    return available
