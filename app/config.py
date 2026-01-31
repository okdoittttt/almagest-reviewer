"""
Github APP에 Configuration settings
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # GitHub App credentials
    github_app_id: str
    github_private_key_path: Path
    github_webhook_secret: str
    github_installation_id: str | None = None

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # .env의 추가 필드 무시
    )

    def read_private_key(self) -> bytes:
        """Read the private key from file"""
        with open(self.github_private_key_path, "rb") as key_file:
            return key_file.read()


# Singleton instance
settings = Settings()