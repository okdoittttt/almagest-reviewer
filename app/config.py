"""
GitHub App 설정 모듈
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경 변수에서 로드되는 애플리케이션 설정.

    Attributes:
        github_app_id: GitHub App ID.
        github_private_key_path: GitHub App 개인키 파일 경로.
        github_webhook_secret: Webhook 서명 검증에 사용되는 시크릿.
        github_installation_id: GitHub App Installation ID (선택).
        llm_provider: 사용할 LLM provider. ``"anthropic"``, ``"google"``, ``"ollama"`` 중 하나.
        anthropic_api_key: Anthropic API 키 (provider가 anthropic인 경우 필수).
        google_api_key: Google API 키 (provider가 google인 경우 필수).
        ollama_base_url: Ollama 서버 주소 (provider가 ollama인 경우 필수).
        ollama_model: Ollama에서 사용할 모델 이름.
        host: 서버 바인딩 주소.
        port: 서버 포트.
    """

    # GitHub App 인증 정보
    github_app_id: str
    github_private_key_path: Path
    github_webhook_secret: str
    github_installation_id: str | None = None

    # LLM 설정
    llm_provider: str = "anthropic"  # 선택지: anthropic, google, ollama
    anthropic_api_key: str | None = None
    google_api_key: str | None = None

    # Ollama (로컬 LLM)
    ollama_base_url: str | None = None
    ollama_model: str = "llama3.2"

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # .env의 추가 필드 무시
    )

    def read_private_key(self) -> bytes:
        """개인키 파일을 읽어 반환합니다.

        Returns:
            PEM 형식의 개인키 바이트.
        """
        with open(self.github_private_key_path, "rb") as key_file:
            return key_file.read()


# 싱글톤 인스턴스
settings = Settings()
