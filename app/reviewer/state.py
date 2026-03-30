"""
LanGraph Review State 정의
"""
from typing import TypedDict, Optional, Annotated
from operator import add

from app.models import PRData


class ReviewState(TypedDict):
    """코드 리뷰 프로세스의 전체 상태를 관리하는 State.

    LanGraph의 각 노드는 이 State를 입력받아 처리하고,
    업데이트된 State를 반환합니다.

    Attributes:
        pr_data: PR 전체 데이터.
        installation_id: GitHub App Installation ID.
        repo_owner: 리포지토리 소유자.
        repo_name: 리포지토리 이름.
        pr_intent: PR 유형, 요약, 목적 등 의도 분석 결과.
            ``type``, ``summary``, ``key_objectives``, ``complexity`` 키를 포함합니다.
        risk_assessment: 위험도 레벨 및 요소.
            ``level`` (LOW/MEDIUM/HIGH), ``score``, ``factors``, ``reasoning`` 키를 포함합니다.
        file_reviews: 파일별 리뷰 결과 목록. 재시도 시 전체 교체됩니다.
        current_file_index: 현재 리뷰 중인 파일 인덱스.
        retry_count: 현재까지 ``review_all_files`` 노드가 실행된 횟수.
        needs_retry: summarizer가 재리뷰 필요 여부를 판단해 설정하는 플래그.
        final_review: 최종 리뷰 코멘트 (마크다운 형식).
        review_decision: 최종 판정. ``"APPROVE"``, ``"REQUEST_CHANGES"``, ``"COMMENT"`` 중 하나.
        messages: LLM 호출 이력. 각 노드 실행 시 누적됩니다 (디버깅용).
        errors: 노드 실행 중 발생한 에러 메시지 목록. 누적됩니다.
    """

    # ===== 입력 데이터 =====
    pr_data: PRData
    installation_id: str
    repo_owner: str
    repo_name: str

    # ===== 0단계: 저장소 Skills + 이전 리뷰 =====
    repo_skills: list[dict]
    repo_system_prompt: Optional[str]
    previous_review: Optional[dict]

    # ===== 1단계: PR 의도 분석 =====
    pr_intent: Optional[dict]

    # ===== 2단계: 위험도 분류 =====
    risk_assessment: Optional[dict]

    # ===== 3단계: 파일별 리뷰 (Loop) =====
    file_reviews: list[dict]

    current_file_index: int

    # ===== 재시도 제어 =====
    retry_count: int
    needs_retry: bool

    # ===== 4단계: 최종 요약 =====
    final_review: Optional[str]
    review_decision: Optional[str]

    # ===== 메타 정보 =====
    messages: Annotated[list[dict], add]
    errors: Annotated[list[str], add]


# 초기 State 생성 헬퍼 함수
def create_initial_state(
    pr_data: PRData,
    installation_id: str,
    repo_owner: str,
    repo_name: str
) -> ReviewState:
    """초기 ReviewState를 생성합니다.

    Args:
        pr_data: PR 데이터.
        installation_id: GitHub App Installation ID.
        repo_owner: 리포지토리 소유자.
        repo_name: 리포지토리 이름.

    Returns:
        모든 분석 필드가 초기값으로 설정된 ReviewState.
    """
    return ReviewState(
        # 입력
        pr_data=pr_data,
        installation_id=installation_id,
        repo_owner=repo_owner,
        repo_name=repo_name,

        # Skills (load_skills 노드가 채움)
        repo_skills=[],
        repo_system_prompt=None,

        # 이전 리뷰 컨텍스트 (load_previous_review 노드가 채움)
        previous_review=None,

        # 분석 결과 (초기값 None)
        pr_intent=None,
        risk_assessment=None,

        # 파일 리뷰 (초기값 빈 리스트)
        file_reviews=[],
        current_file_index=0,

        # 재시도 제어
        retry_count=0,
        needs_retry=False,

        # 최종 결과 (초기값 None)
        final_review=None,
        review_decision=None,

        # 메타
        messages=[],
        errors=[]
    )
