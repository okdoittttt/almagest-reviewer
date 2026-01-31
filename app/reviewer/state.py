"""
LanGraph Review State 정의
"""
from typing import TypedDict, Optional, Annotated
from operator import add

from app.models import PRData


class ReviewState(TypedDict):
    """
    코드 리뷰 프로세스의 전체 상태를 관리하는 State

    LanGraph의 각 노드는 이 State를 입력받아 처리하고,
    업데이트된 State를 반환합니다.
    """

    # ===== 입력 데이터 =====
    pr_data: PRData                    # PR 전체 데이터
    installation_id: str               # GitHub App Installation ID
    repo_owner: str                    # 리포지토리 소유자
    repo_name: str                     # 리포지토리 이름

    # ===== 1단계: PR 의도 분석 =====
    pr_intent: Optional[dict]          # PR 유형, 요약, 목적 등
    # 예시: {
    #   "type": "feature" | "bugfix" | "refactor" | "docs",
    #   "summary": "사용자 인증 기능 추가",
    #   "key_objectives": ["로그인 API 구현", "JWT 토큰 발급"],
    #   "complexity": "medium"
    # }

    # ===== 2단계: 위험도 분류 =====
    risk_assessment: Optional[dict]    # 위험도 레벨 및 요소
    # 예시: {
    #   "level": "LOW" | "MEDIUM" | "HIGH",
    #   "factors": ["large_changes", "critical_file: auth.py"],
    #   "reasoning": "인증 관련 파일이 수정되어 높은 주의가 필요함",
    #   "needs_careful_review": True
    # }

    # ===== 3단계: 파일별 리뷰 (Loop) =====
    file_reviews: Annotated[list[dict], add]  # 파일별 리뷰 결과 (누적)
    # 예시: [
    #   {
    #     "filename": "src/auth.py",
    #     "issues": [
    #       {"severity": "high", "line": 42, "message": "SQL injection 가능성"},
    #       {"severity": "low", "line": 58, "message": "변수명이 명확하지 않음"}
    #     ],
    #     "suggestions": ["입력 검증 추가", "변수명을 더 명확하게"],
    #     "status": "NEEDS_CHANGES" | "LGTM",
    #     "raw_review": "LLM의 원본 응답"
    #   }
    # ]

    current_file_index: int            # 현재 리뷰 중인 파일 인덱스

    # ===== 4단계: 최종 요약 =====
    final_review: Optional[str]        # 최종 리뷰 코멘트 (마크다운)
    review_decision: Optional[str]     # "APPROVE" | "REQUEST_CHANGES" | "COMMENT"

    # ===== 메타 정보 =====
    messages: Annotated[list[dict], add]  # LLM 호출 이력 (디버깅용)
    # 예시: [
    #   {"role": "intent_analyzer", "content": "...", "timestamp": "..."},
    #   {"role": "risk_classifier", "content": "...", "timestamp": "..."}
    # ]

    errors: Annotated[list[str], add]  # 에러 발생 시 기록


# 초기 State 생성 헬퍼 함수
def create_initial_state(
    pr_data: PRData,
    installation_id: str,
    repo_owner: str,
    repo_name: str
) -> ReviewState:
    """
    초기 ReviewState 생성

    Args:
        pr_data: PR 데이터
        installation_id: Installation ID
        repo_owner: 리포지토리 소유자
        repo_name: 리포지토리 이름

    Returns:
        초기화된 ReviewState
    """
    return ReviewState(
        # 입력
        pr_data=pr_data,
        installation_id=installation_id,
        repo_owner=repo_owner,
        repo_name=repo_name,

        # 분석 결과 (초기값 None)
        pr_intent=None,
        risk_assessment=None,

        # 파일 리뷰 (초기값 빈 리스트)
        file_reviews=[],
        current_file_index=0,

        # 최종 결과 (초기값 None)
        final_review=None,
        review_decision=None,

        # 메타
        messages=[],
        errors=[]
    )
