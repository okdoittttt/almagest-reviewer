"""
JWT 토큰 생성 테스트
"""
from app.config import settings
from app.auth import generate_jwt


def test_jwt():
    print("=== JWT 토큰 생성 테스트 ===")
    print(f"App ID: {settings.github_app_id}")
    print(f"Private Key Path: {settings.github_private_key_path}")

    # Private key 읽기
    private_key = settings.read_private_key()
    print(f"Private Key 읽기 성공 (크기: {len(private_key)} bytes)")

    # JWT 생성
    jwt_token = generate_jwt(
        app_id=settings.github_app_id,
        private_key=private_key,
        expiration_seconds=600
    )

    print(f"✅ JWT 토큰 생성 성공!")
    print(f"토큰: {jwt_token[:50]}...")
    print(f"토큰 길이: {len(jwt_token)}")


if __name__ == "__main__":
    test_jwt()
