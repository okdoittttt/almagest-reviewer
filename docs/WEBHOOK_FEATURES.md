# GitHub 웹훅 추가 기능 설계

현재 `pull_request` 이벤트의 `opened`, `synchronize`, `closed`만 처리 중. 아래 4가지 기능을 단계적으로 추가한다.

---

## ✅ 선행 작업: 핸들러 모듈 분리 (리팩터링) — 완료

`main.py`에 뭉쳐 있는 웹훅 라우팅을 모듈로 분리한다.

### 목표 구조

```
app/webhook/
    __init__.py
    validator.py         (변경 없음)
    dispatcher.py        (신규)
    handlers/
        __init__.py
        _helpers.py      (공유 파이프라인 함수)
        pull_request.py  (Feature 1, 4)
        installation.py  (Feature 2)
        issue_comment.py (Feature 3)
```

### `_helpers.py` — 공유 파이프라인 함수

현재 `main.py`에 inline된 "PR 데이터 수집 → LangGraph → DB 저장 → GitHub 코멘트" 시퀀스를 추출:

```python
async def run_full_review_pipeline(
    session: AsyncSession,
    installation_id: str,
    github_repo_id: int,
    github_pr_id: int,
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    trigger_source: str = "push",
) -> None
```

### `main.py` 최종 형태

```python
@app.post("/webhook")
async def github_webhook(request: Request, session: AsyncSession = Depends(get_db)):
    verified_body = await verify_webhook_signature(request)
    payload = json.loads(verified_body)
    event = request.headers.get("x-github-event", "unknown")
    action = payload.get("action", "none")
    await dispatch_event(event, action, payload, session)
    return JSONResponse({"status": "success"})
```

---

## Feature 1: `pull_request.ready_for_review` + 드래프트 가드

### 배경
드래프트 PR이 `opened`될 때 불필요한 리뷰가 실행됨.

### 이벤트
`pull_request`, action: `ready_for_review`

### 구현

**드래프트 가드 추가 (`opened`):**
```python
if action == "opened" and payload["pull_request"]["draft"]:
    logger.info("드래프트 PR, 리뷰 건너뜀")
    return
```

**`ready_for_review` 라우팅 추가:**
```python
elif action == "ready_for_review":
    await run_full_review_pipeline(..., trigger_source="ready_for_review")
```

### 엣지케이스
- `ready_for_review` 직전에 `synchronize`가 이미 왔다면 같은 `head_sha`로 중복 리뷰 가능 → 파이프라인 실행 전 해당 `head_sha`로 `Review` 레코드가 이미 있으면 스킵
- `synchronize` 이벤트에는 드래프트 가드 미적용 (드래프트 상태에서 커밋 푸시는 `ready_for_review` 시점에 처리)

### 신규 서비스 함수
```python
# app/services/review_service.py
async def review_exists_for_head_sha(
    session: AsyncSession,
    github_repo_id: int,
    pr_number: int,
    head_sha: str,
) -> bool
```
`Review` → `PullRequest` → `Repository` 조인으로 동일 `head_sha` 리뷰 존재 여부 확인.

### DB 변경
없음

---

## Feature 2: `installation` / `installation_repositories` — 레포 자동 등록

### 배경
앱 설치 시 레포지토리를 수동으로 DB에 등록해야 함.

### 이벤트
- `installation`, action: `created` / `deleted`
- `installation_repositories`, action: `added` / `removed`

### 구현 (`app/webhook/handlers/installation.py`)

| 이벤트 | 처리 |
|--------|------|
| `installation.created` | `payload["repositories"]` 순회 → `upsert_repository()` |
| `installation.deleted` | `payload["repositories"]` 순회 → `is_active = False` |
| `installation_repositories.added` | `payload["repositories_added"]` 순회 → `upsert_repository()` |
| `installation_repositories.removed` | `payload["repositories_removed"]` 순회 → `is_active = False` |

**신규 서비스 함수 (`app/services/review_service.py`):**
```python
async def deactivate_repositories(
    session: AsyncSession,
    github_repo_ids: list[int],
) -> int
```
레코드 삭제 안 함 — 리뷰 히스토리 보존.

### 엣지케이스
- "전체 레포" 권한으로 설치 시 `payload["repositories"]`가 빈 리스트 → 경고 로그만 남기고 리턴 (첫 PR 웹훅에서 `upsert_repository`로 자동 등록됨)

### DB 변경
없음 (`repositories.is_active` 이미 존재)

---

## Feature 3: `issue_comment` → `/re-review` 커맨드

### 배경
새 커밋 없이 리뷰를 재트리거할 방법이 없음.

### 이벤트
`issue_comment`, action: `created`

### 구현 (`app/webhook/handlers/issue_comment.py`)

```python
REVIEW_COOLDOWN_SECONDS = 60
ALLOWED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}

async def handle_issue_comment(action, payload, session):
    # 1. PR 코멘트인지 확인
    if "pull_request" not in payload["issue"]:
        return
    # 2. 닫힌 PR 스킵
    if payload["issue"]["state"] == "closed":
        return
    # 3. /re-review 커맨드 확인
    if "/re-review" not in payload["comment"]["body"].lower():
        return
    # 4. 권한 검사
    author_association = payload["comment"]["author_association"]
    commenter_login = payload["comment"]["user"]["login"]
    pr_author_login = payload["issue"]["user"]["login"]
    is_authorized = (
        author_association in ALLOWED_ASSOCIATIONS
        or commenter_login == pr_author_login
    )
    if not is_authorized:
        # GitHub에 권한 없음 안내 코멘트 후 리턴
        return
    # 5. 쿨다운 체크 (최근 60초 이내 리뷰 실행됐으면 스킵)
    # ...
    # 6. 현재 head_sha 조회 (GitHub API)
    pr_details = await github_client.get_pr_details(...)
    # 7. 파이프라인 실행
    await run_full_review_pipeline(..., trigger_source="re_review_command")
```

### 권한 검사 상세

`payload["comment"]["author_association"]` 필드를 활용 — 별도 GitHub API 호출 없이 페이로드에서 직접 판단.

| author_association | 허용 여부 |
|--------------------|-----------|
| `OWNER` | ✅ |
| `MEMBER` | ✅ |
| `COLLABORATOR` | ✅ |
| `CONTRIBUTOR` / `NONE` 등 | ❌ (PR 작성자 본인은 예외적으로 허용) |

미인가 시 GitHub에 안내 코멘트 게시:
> `/re-review 커맨드는 저장소 협력자 또는 PR 작성자만 실행할 수 있습니다.`

### 신규 서비스 함수
```python
# app/services/review_service.py
async def get_most_recent_review(
    session: AsyncSession,
    github_repo_id: int,
    pr_number: int,
) -> Review | None
```
쿨다운 체크 시 최근 리뷰 생성 시각 조회에 사용.

### 엣지케이스
- 60초 이내 재시도 → GitHub에 쿨다운 안내 코멘트 후 리턴
- `issue_comment` payload에 `github_pr_id` 없음 → `get_pr_details()`로 조회 필요
- 비인가 사용자 → GitHub에 안내 코멘트 후 리턴 (DoS 방지)

### DB 변경
없음

---

## Feature 4: `pull_request.labeled` / `pull_request.unlabeled`

### 배경
`wip`, `skip-review` 라벨 붙은 PR도 리뷰가 실행됨.

### 이벤트
`pull_request`, action: `labeled` / `unlabeled`

### 구현 (`app/webhook/handlers/pull_request.py`)

```python
SKIP_REVIEW_LABELS = {"skip-review", "wip"}

# labeled 처리
if payload["label"]["name"].lower() in SKIP_REVIEW_LABELS:
    # GitHub에 "스킵 라벨로 인해 리뷰 건너뜀" 코멘트
    return

# unlabeled 처리
if payload["label"]["name"].lower() in SKIP_REVIEW_LABELS:
    # 다른 스킵 라벨이 남아있는지 GitHub API로 확인
    pr_details = await github_client.get_pr_details(...)
    current_labels = {l["name"].lower() for l in pr_details.get("labels", [])}
    if current_labels & SKIP_REVIEW_LABELS:
        return  # 여전히 스킵 라벨 있음
    if not pr_details.get("draft"):
        await run_full_review_pipeline(..., trigger_source="label_removed")
```

### 엣지케이스
- 복수 스킵 라벨: `wip` 제거해도 `skip-review` 남아있으면 리뷰 안 함 → GitHub API로 현재 라벨 재조회로 해결
- 드래프트 PR에 라벨 추가/제거: 드래프트면 무시 (`ready_for_review`에서 처리)
- `unlabeled` 시 `pr_details`를 재조회하는 이유: payload의 `pull_request.labels`는 제거 전 목록을 반영하지 않을 수 있음

### DB 변경
없음 (라벨 상태는 GitHub API 소스 오브 트루스)

---

## Optional: `reviews.trigger_source` 컬럼

마이그레이션: `alembic/versions/0003_add_review_trigger_source.py`

`reviews` 테이블에 `trigger_source VARCHAR(50) DEFAULT 'push'` 추가.

| 값 | 트리거 상황 |
|----|------------|
| `push` | 커밋 푸시 (`synchronize`) 또는 PR `opened` |
| `ready_for_review` | 드래프트 → 일반 PR 전환 |
| `re_review_command` | `/re-review` 커맨드 |
| `label_removed` | 스킵 라벨 제거 |

nullable + server default → 기존 데이터 호환성 보장.

---

## AI 자동 `is_addressed` 업데이트

### 배경
기존에는 `ReviewComment.is_addressed`를 사람이 UI에서 직접 체크해야만 `True`로 변경됐다.
`is_addressed=False` 코멘트는 다음 리뷰 프롬프트에 그대로 포함되기 때문에, 개발자가 실제로 이슈를 고쳤어도 수동으로 체크하지 않으면 불필요한 입력 토큰이 계속 소모된다.

### 구현 흐름

```
1. load_previous_review 노드
   → 미해결 코멘트 로드 시 comment.id 포함
   { "id": 42, "type": "issue", "body": "..." }

2. review_prompt (파일별)
   → 프롬프트에 #id 표시
   "- [#42][issue] Some issue body"
   → 해결된 ID를 resolved_comment_ids에 출력하도록 지시

3. file_reviewer 노드
   → AI 응답에서 resolved_comment_ids 파싱
   { "resolved_comment_ids": [42], "status": "LGTM", ... }

4. _helpers.py (run_full_review_pipeline)
   → 리뷰 완료 후 persist_review_result 호출 전에 실행
   resolved_ids = [id for fr in file_reviews for id in fr.get("resolved_comment_ids", [])]
   await mark_comments_addressed(session, resolved_ids)

5. 다음 push 시 load_previous_review
   → #42는 is_addressed=True라 프롬프트에서 자동 제외
   → 토큰 낭비 없음
```

### 수정 파일

| 파일 | 변경 내용 |
|------|-----------|
| `app/reviewer/nodes/previous_review_loader.py` | 코멘트 dict에 `id` 필드 추가 |
| `app/reviewer/prompts/review_prompt.py` | 미해결 이슈를 `[#id][type]` 형식으로 표시, `resolved_comment_ids` 출력 지시 추가 |
| `app/reviewer/nodes/file_reviewer.py` | `resolved_comment_ids` 기본값(`[]`) 파싱 추가 |
| `app/services/review_service.py` | `mark_comments_addressed()` 추가 |
| `app/webhook/handlers/_helpers.py` | 리뷰 후 자동 업데이트 로직 추가 |

### 신규 서비스 함수
```python
# app/services/review_service.py
async def mark_comments_addressed(
    session: AsyncSession,
    comment_ids: list[int],
) -> int
```
`UPDATE review_comments SET is_addressed=True, addressed_at=now() WHERE id IN (...)`

### DB 변경
없음 (`is_addressed`, `addressed_at` 컬럼 이미 존재)

---

## 프론트엔드 변경: `trigger_source` 표시

### 배경
리뷰 상세 화면에서 해당 리뷰가 어떤 이유로 트리거됐는지 확인할 수 없었음.

### 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/src/api/types.ts` | `Review` 인터페이스에 `trigger_source: string` 추가 |
| `frontend/src/components/Badge.tsx` | `TriggerSourceBadge` 컴포넌트 추가 (보라색 배지) |
| `frontend/src/pages/ReviewDetail.tsx` | 리뷰 헤더에 `TriggerSourceBadge` 표시 |

### `TriggerSourceBadge` 표시 값

| trigger_source | 표시 텍스트 |
|----------------|------------|
| `push` | 커밋 |
| `ready_for_review` | Ready for Review |
| `re_review_command` | /re-review |
| `label_removed` | 라벨 제거 |

---

## 구현 순서

| 단계 | 작업 | 난이도 | 상태 |
|------|------|--------|------|
| 0 | `main.py` → 핸들러 모듈 리팩터링 (동작 변경 없음) | 낮음 | ✅ 완료 |
| 1 | Feature 1: `ready_for_review` + 드래프트 가드 | 낮음 | ✅ 완료 |
| 2 | Feature 2: `installation` 레포 자동 등록 | 낮음 | ✅ 완료 |
| 3 | Feature 4: `labeled`/`unlabeled` 스킵 | 낮음 | ✅ 완료 |
| 4 | Feature 3: `/re-review` 커맨드 (쿨다운 + 권한 검사 포함) | 중간 | ✅ 완료 |
| 5 | Optional: `trigger_source` 마이그레이션 | 낮음 | ✅ 완료 |
| 6 | 프론트엔드: `trigger_source` 배지 표시 | 낮음 | ✅ 완료 |
| 7 | AI 자동 `is_addressed` 업데이트 | 중간 | ✅ 완료 |

---

## 수정 대상 파일

### 백엔드 — 웹훅 핸들러

| 파일 | 변경 유형 | 상태 |
|------|-----------|------|
| `main.py` | 리팩터링 (thin dispatcher로 축소) | ✅ 완료 |
| `app/webhook/dispatcher.py` | 신규 | ✅ 완료 |
| `app/webhook/handlers/__init__.py` | 핸들러 export 관리 | ✅ 완료 |
| `app/webhook/handlers/_helpers.py` | 신규, AI 자동 is_addressed 업데이트 추가 | ✅ 완료 |
| `app/webhook/handlers/pull_request.py` | 신규 (Feature 1, 4) | ✅ 완료 |
| `app/webhook/handlers/installation.py` | 신규 (Feature 2) | ✅ 완료 |
| `app/webhook/handlers/issue_comment.py` | 신규 (Feature 3, 권한 검사 포함) | ✅ 완료 |

### 백엔드 — 서비스 / 모델 / 마이그레이션

| 파일 | 변경 유형 | 상태 |
|------|-----------|------|
| `app/services/review_service.py` | `deactivate_repositories`, `review_exists_for_head_sha`, `get_most_recent_review`, `mark_comments_addressed` 추가 | ✅ 완료 |
| `app/database/models/review.py` | `trigger_source` 컬럼 추가 | ✅ 완료 |
| `alembic/versions/0003_add_review_trigger_source.py` | 신규 마이그레이션 | ✅ 완료 |

### 백엔드 — LangGraph 리뷰어

| 파일 | 변경 유형 | 상태 |
|------|-----------|------|
| `app/reviewer/nodes/previous_review_loader.py` | 코멘트 dict에 `id` 필드 추가 | ✅ 완료 |
| `app/reviewer/nodes/file_reviewer.py` | `resolved_comment_ids` 파싱 추가 | ✅ 완료 |
| `app/reviewer/prompts/review_prompt.py` | `[#id]` 표시 및 `resolved_comment_ids` 출력 지시 추가 | ✅ 완료 |

### 프론트엔드

| 파일 | 변경 유형 | 상태 |
|------|-----------|------|
| `frontend/src/api/types.ts` | `Review.trigger_source` 필드 추가 | ✅ 완료 |
| `frontend/src/components/Badge.tsx` | `TriggerSourceBadge` 컴포넌트 추가 | ✅ 완료 |
| `frontend/src/pages/ReviewDetail.tsx` | 리뷰 헤더에 `TriggerSourceBadge` 추가 | ✅ 완료 |

### 테스트

| 파일 | 변경 유형 | 상태 |
|------|-----------|------|
| `tests/test_pull_request_handler.py` | 신규 (Feature 1 단위 테스트 6개) | ✅ 완료 |
| `tests/test_labeled_handler.py` | 신규 (Feature 4 단위 테스트 7개) | ✅ 완료 |
| `tests/test_issue_comment_handler.py` | 신규 (Feature 3 단위 테스트 11개, 권한 검사 포함) | ✅ 완료 |

---

## 검증 방법

1. **기존 동작 확인:** 리팩터링 후 기존 PR 열기/업데이트/닫기 흐름 동일한지 확인
2. **Feature 1:** 드래프트 PR 열기 → 리뷰 없음 → "Ready for review" → 리뷰 실행; `synchronize` 직후 "Ready for review" → 중복 스킵
3. **Feature 2:** GitHub App Settings에서 레포 추가/제거 → DB `is_active` 변경 확인
4. **Feature 3:** PR에 `/re-review` 코멘트 → 리뷰 재실행; 60초 이내 재시도 → 쿨다운 코멘트; 외부 기여자가 커맨드 입력 → 권한 없음 코멘트
5. **Feature 4:** `wip` 라벨 추가 → 스킵 코멘트; 라벨 제거 → 리뷰 실행; `wip` + `skip-review` 둘 다 있을 때 하나만 제거 → 리뷰 안 함
6. **trigger_source:** 각 트리거 시나리오 후 DB `reviews.trigger_source` 값 및 프론트엔드 배지 확인
7. **AI 자동 is_addressed:** 이전 리뷰 이슈 수정 후 push → 서버 로그 `해결된 이전 이슈 N개 자동 처리` 확인 → DB `review_comments.is_addressed=True` 확인 → 다음 push 시 해당 이슈 프롬프트에서 제외됨 확인
8. **단위 테스트:** `pytest tests/test_pull_request_handler.py tests/test_labeled_handler.py tests/test_issue_comment_handler.py -v` — 24개 통과

---

## 배포 시 주의사항

- **DB 마이그레이션 필요:** `alembic upgrade head` 실행 (`trigger_source` 컬럼 추가)
- 기존 `reviews` 레코드는 `trigger_source='push'`로 자동 채워짐 (server_default)
