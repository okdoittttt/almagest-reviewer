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
        database_url: SQLAlchemy async 데이터베이스 URL.
        host: 서버 바인딩 주소.
        port: 서버 포트.
    """

    # GitHub App 인증 정보
    github_app_id: str
    github_app_name: str = ""
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

    # diff 크기 제한 (HIGH 위험도 기준 최대값, LOW=30% / MEDIUM=70% / HIGH=100% 비율 적용)
    diff_max_chars_cloud: int = 10000   # anthropic / google
    diff_max_chars_ollama: int = 4000   # ollama (로컬 LLM 컨텍스트 창 고려)

    # 데이터베이스
    database_url: str = "postgresql+asyncpg://almagest:almagest@db:5432/almagest_reviewer"

    # OAuth 로그인 (GitHub App > Settings > Client ID / Client Secret)
    github_client_id: str = ""
    github_client_secret: str = ""
    # 접근 허용할 GitHub 로그인명, 콤마 구분 (예: "okdoittttt,teammate")
    allowed_github_users: str = ""
    # 접근 허용할 GitHub Organization 이름 (예: "my-org"). 설정 시 org 멤버 전원 허용
    allowed_github_org: str = ""
    # 앱 베이스 URL (OAuth redirect_uri 생성에 사용)
    # 로컬: http://localhost:8000 / 배포: https://reviewer.okdoitttt.com
    app_base_url: str = "http://localhost:8000"

    # JWT 서명 키
    jwt_secret: str = "change-me-please"
    jwt_expire_hours: int = 72

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
