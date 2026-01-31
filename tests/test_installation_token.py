"""
Installation Token 발급 테스트
"""
import asyncio
from app.config import settings
from app.github import GitHubClient


async def test_installation_token():
    print("=== Installation Token 발급 테스트 ===")

    client = GitHubClient()

    # Installation token 발급
    token = await client.get_installation_token(settings.github_installation_id)

    print(f"✅ Installation Token 발급 성공!")
    print(f"토큰: {token[:20]}...")
    print(f"토큰 길이: {len(token)}")


if __name__ == "__main__":
    asyncio.run(test_installation_token())
