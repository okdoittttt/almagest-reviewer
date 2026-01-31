"""
Risk Assessment Prompt
"""
from app.models import PRData


def create_risk_assessment_prompt(pr_data: PRData, pr_intent: dict) -> str:
    """
    변경의 위험도를 평가하는 프롬프트 생성

    Args:
        pr_data: PR 데이터
        pr_intent: PR 의도 분석 결과

    Returns:
        프롬프트 문자열
    """
    # 파일별 변경 요약
    files_by_type = {}
    for file in pr_data.files:
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'other'
        if ext not in files_by_type:
            files_by_type[ext] = []
        files_by_type[ext].append(file)

    files_summary = "\n".join([
        f"- `.{ext}` 파일: {len(files)}개"
        for ext, files in files_by_type.items()
    ])

    # 중요 파일 탐지
    critical_keywords = [
        'auth', 'security', 'password', 'token', 'payment', 'billing',
        'migration', 'database', 'db', 'schema', 'admin', 'permission'
    ]

    critical_files = []
    for file in pr_data.files:
        filename_lower = file.filename.lower()
        matched_keywords = [kw for kw in critical_keywords if kw in filename_lower]
        if matched_keywords:
            critical_files.append(f"- {file.filename} (keywords: {', '.join(matched_keywords)})")

    critical_files_text = "\n".join(critical_files) if critical_files else "(없음)"

    # 테스트 파일 체크
    test_files = [f for f in pr_data.files if 'test' in f.filename.lower() or f.filename.startswith('test_')]
    test_coverage_note = f"{len(test_files)}개의 테스트 파일이 변경됨" if test_files else "⚠️ 테스트 파일 변경 없음"

    return f"""당신은 보안과 안정성을 중시하는 시니어 개발자입니다. 다음 PR의 위험도를 평가해주세요.

## PR 의도 (이전 단계 분석 결과)
- 유형: {pr_intent.get('type', 'unknown')}
- 요약: {pr_intent.get('summary', 'N/A')}
- 복잡도: {pr_intent.get('complexity', 'unknown')}

## 변경 통계
- 전체 변경: {pr_data.total_changes} 줄 (+{pr_data.total_additions}/-{pr_data.total_deletions})
- 파일 개수: {pr_data.changed_files_count}개
- 커밋 개수: {pr_data.commits_count}개

## 파일 유형별 분포
{files_summary}

## 중요 파일 감지 (인증, 보안, 결제, DB 등)
{critical_files_text}

## 테스트 커버리지
{test_coverage_note}

## 변경된 파일 목록
{chr(10).join([f"- {f.filename} ({f.status}, +{f.additions}/-{f.deletions})" for f in pr_data.files[:15]])}
{f"... 외 {pr_data.changed_files_count - 15}개 파일" if pr_data.changed_files_count > 15 else ""}

---

다음 형식으로 JSON 응답을 제공해주세요:

```json
{{
  "level": "LOW | MEDIUM | HIGH",
  "score": 1-10,
  "factors": [
    "large_changes",
    "critical_file_modified",
    "no_tests",
    "database_changes"
  ],
  "reasoning": "위험도 판단의 상세한 근거",
  "needs_careful_review": true,
  "review_focus_areas": [
    "인증 로직 보안 검토",
    "에러 처리 확인",
    "성능 영향도 평가"
  ]
}}
```

**평가 기준:**
1. **LOW (1-3점)**: 문서 수정, 작은 버그 수정, 테스트 추가 등
2. **MEDIUM (4-7점)**: 기능 추가, 리팩토링, 중간 규모 변경
3. **HIGH (8-10점)**: 인증/보안 변경, 대규모 리팩토링, DB 스키마 변경, 테스트 없는 중요 변경

**위험 요소:**
- 변경량 (500줄 이상: 위험)
- 중요 파일 수정 (auth, security, payment 등)
- 테스트 부재
- 복잡한 로직 변경

JSON만 응답해주세요."""
