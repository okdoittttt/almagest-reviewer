"""
Webhook 엔드포인트 통합 테스트
"""
import json
import asyncio
import httpx

from app.config import settings
from app.webhook.validator import calculate_signature


async def test_webhook_with_valid_signature():
    """유효한 서명으로 Webhook 요청 테스트"""
    print("=== 유효한 서명 테스트 ===")

    # 테스트 페이로드
    payload = {
        "action": "opened",
        "installation": {"id": settings.github_installation_id},
        "repository": {
            "name": "test-repo",
            "owner": {"login": "test-user"}
        },
        "pull_request": {
            "number": 1,
            "title": "Test PR"
        }
    }

    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_bytes = payload_json.encode('utf-8')

    # 올바른 서명 생성
    signature = calculate_signature(settings.github_webhook_secret, payload_bytes)

    print(f"Payload: {payload_json[:100]}...")
    print(f"Signature: {signature[:50]}...")

    # HTTP 요청
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/github/webhook",
                content=payload_bytes,
                headers={
                    "X-Hub-Signature-256": signature,
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 200:
                print("✅ 유효한 서명 테스트 통과!")
            else:
                print(f"❌ 예상치 못한 응답: {response.status_code}")

        except httpx.ConnectError:
            print("❌ 서버가 실행되지 않았습니다. 먼저 서버를 실행하세요:")
            print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")


async def test_webhook_with_invalid_signature():
    """잘못된 서명으로 Webhook 요청 테스트"""
    print("\n=== 잘못된 서명 테스트 ===")

    payload = {"action": "opened"}
    payload_bytes = json.dumps(payload).encode('utf-8')

    # 잘못된 서명
    wrong_signature = "sha256=wrong_signature_12345"

    print(f"Wrong Signature: {wrong_signature}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/github/webhook",
                content=payload_bytes,
                headers={
                    "X-Hub-Signature-256": wrong_signature,
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 403:
                print("✅ 잘못된 서명 거부 성공!")
            else:
                print(f"❌ 예상치 못한 응답: {response.status_code}")

        except httpx.ConnectError:
            print("❌ 서버가 실행되지 않았습니다.")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")


async def test_webhook_without_signature():
    """서명 없이 Webhook 요청 테스트"""
    print("\n=== 서명 없음 테스트 ===")

    payload = {"action": "opened"}
    payload_bytes = json.dumps(payload).encode('utf-8')

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/github/webhook",
                content=payload_bytes,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 403:
                print("✅ 서명 없음 거부 성공!")
            else:
                print(f"❌ 예상치 못한 응답: {response.status_code}")

        except httpx.ConnectError:
            print("❌ 서버가 실행되지 않았습니다.")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")


async def main():
    print("🚀 Webhook 엔드포인트 통합 테스트 시작\n")
    print("📌 서버가 실행 중인지 확인하세요:")
    print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000\n")

    await test_webhook_with_valid_signature()
    await test_webhook_with_invalid_signature()
    await test_webhook_without_signature()

    print("\n🎉 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
