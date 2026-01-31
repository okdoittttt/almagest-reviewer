"""
Webhook 서명 검증 테스트
"""
import hmac
import hashlib
import json

from app.config import settings
from app.webhook.validator import calculate_signature, verify_signature


def test_signature_calculation():
    """서명 계산 테스트"""
    print("=== Webhook 서명 계산 테스트 ===")

    # 테스트 데이터
    secret = "test-secret"
    payload_dict = {"test": "data", "number": 123}
    payload_bytes = json.dumps(payload_dict).encode('utf-8')

    # 서명 계산
    signature = calculate_signature(secret, payload_bytes)

    print(f"Secret: {secret}")
    print(f"Payload: {payload_dict}")
    print(f"계산된 서명: {signature}")
    print(f"서명 형식 확인: {signature.startswith('sha256=')}")

    # 수동 계산으로 검증
    expected = "sha256=" + hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    print(f"예상 서명: {expected}")
    print(f"일치 여부: {signature == expected}")

    assert signature == expected, "서명 계산 오류"
    print("✅ 서명 계산 테스트 통과!")


def test_signature_verification():
    """서명 검증 테스트"""
    print("\n=== Webhook 서명 검증 테스트 ===")

    secret = "test-secret"
    payload = b'{"action":"opened","number":1}'

    # 올바른 서명 생성
    correct_signature = calculate_signature(secret, payload)
    print(f"올바른 서명: {correct_signature[:30]}...")

    # 검증 테스트 - 성공 케이스
    is_valid = verify_signature(correct_signature, correct_signature)
    print(f"동일한 서명 검증: {is_valid}")
    assert is_valid, "동일한 서명은 검증을 통과해야 함"

    # 검증 테스트 - 실패 케이스
    wrong_signature = "sha256=wrong_signature_here"
    is_invalid = verify_signature(wrong_signature, correct_signature)
    print(f"잘못된 서명 검증: {is_invalid}")
    assert not is_invalid, "잘못된 서명은 검증을 실패해야 함"

    # 검증 테스트 - 헤더 없음
    is_none = verify_signature(None, correct_signature)
    print(f"헤더 없음 검증: {is_none}")
    assert not is_none, "헤더가 없으면 검증을 실패해야 함"

    print("✅ 서명 검증 테스트 통과!")


def test_real_webhook_secret():
    """실제 Webhook Secret으로 서명 생성 테스트"""
    print("\n=== 실제 Webhook Secret 테스트 ===")

    print(f"Webhook Secret: {settings.github_webhook_secret}")

    # 예시 GitHub PR 이벤트
    example_payload = {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "title": "Test PR",
            "number": 1
        }
    }

    payload_bytes = json.dumps(example_payload, separators=(',', ':')).encode('utf-8')

    # 서명 생성
    signature = calculate_signature(settings.github_webhook_secret, payload_bytes)

    print(f"생성된 서명: {signature[:50]}...")
    print(f"서명 길이: {len(signature)}")

    # 이 서명을 HTTP 요청의 X-Hub-Signature-256 헤더에 넣으면 됩니다
    print("\n💡 HTTP 요청 시 다음 헤더를 추가하세요:")
    print(f"  X-Hub-Signature-256: {signature}")

    print("✅ 실제 Secret 테스트 통과!")


if __name__ == "__main__":
    test_signature_calculation()
    test_signature_verification()
    test_real_webhook_secret()
    print("\n🎉 모든 테스트 통과!")
