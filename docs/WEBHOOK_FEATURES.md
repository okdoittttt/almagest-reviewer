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
    await run_full_review_pipeline(...)
```

### 엣지케이스
- `ready_for_review` 직전에 `synchronize`가 이미 왔다면 같은 `head_sha`로 중복 리뷰 가능 → 파이프라인 실행 전 해당 `head_sha`로 `Review` 레코드가 이미 있으면 스킵

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
    # 4. 쿨다운 체크 (최근 60초 이내 리뷰 실행됐으면 스킵)
    # ...
    # 5. 현재 head_sha 조회 (GitHub API)
    pr_details = await github_client.get_pr_details(...)
    # 6. 파이프라인 실행
    await run_full_review_pipeline(..., trigger_source="re_review_command")
```

### 엣지케이스
- 60초 이내 재시도 → GitHub에 쿨다운 안내 코멘트 후 리턴
- `issue_comment` payload에 `github_pr_id` 없음 → `get_pr_details()`로 조회 필요

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
    if not payload["pull_request"]["draft"]:
        await run_full_review_pipeline(...)
```

### 엣지케이스
- 복수 스킵 라벨: `wip` 제거해도 `skip-review` 남아있으면 리뷰 안 함 → GitHub API로 현재 라벨 재조회로 해결
- 드래프트 PR에 라벨 추가/제거: 드래프트면 무시 (`ready_for_review`에서 처리)

### DB 변경
없음 (라벨 상태는 GitHub API 소스 오브 트루스)

---

## Optional: `reviews.trigger_source` 컬럼

마이그레이션: `alembic/versions/0003_add_review_trigger_source.py`

`reviews` 테이블에 `trigger_source VARCHAR(50) DEFAULT 'push'` 추가.
값: `push`, `re_review_command`, `ready_for_review`, `label_removed`

nullable + server default → 기존 데이터 호환성 보장.

---

## 구현 순서

| 단계 | 작업 | 난이도 | 상태 |
|------|------|--------|------|
| 0 | `main.py` → 핸들러 모듈 리팩터링 (동작 변경 없음) | 낮음 | ✅ 완료 |
| 1 | Feature 1: `ready_for_review` + 드래프트 가드 | 낮음 | ✅ 완료 |
| 2 | Feature 2: `installation` 레포 자동 등록 | 낮음 | ✅ 완료 |
| 3 | Feature 4: `labeled`/`unlabeled` 스킵 | 낮음 | ✅ 완료 |
| 4 | Feature 3: `/re-review` 커맨드 (쿨다운 포함) | 중간 | ✅ 완료 |
| 5 | Optional: `trigger_source` 마이그레이션 | 낮음 | ✅ 완료 |

---

## 수정 대상 파일

| 파일 | 변경 유형 | 상태 |
|------|-----------|------|
| `main.py` | 리팩터링 (thin dispatcher로 축소) | ✅ 완료 |
| `app/webhook/dispatcher.py` | 신규 | ✅ 완료 |
| `app/webhook/handlers/_helpers.py` | 신규 | ✅ 완료 |
| `app/webhook/handlers/pull_request.py` | 신규 (Feature 1, 4) | ✅ 완료 |
| `app/webhook/handlers/installation.py` | 신규 (Feature 2) | ✅ 완료 |
| `app/webhook/handlers/issue_comment.py` | 신규 (Feature 3) | ✅ 완료 |
| `app/services/review_service.py` | `deactivate_repositories`, `review_exists_for_head_sha`, `get_most_recent_review` 추가 | ✅ 완료 |
| `app/database/models/review.py` | `trigger_source` 컬럼 추가 | ✅ 완료 |
| `alembic/versions/0003_add_review_trigger_source.py` | 신규 마이그레이션 | ✅ 완료 |

---

## 검증 방법

1. **기존 동작 확인:** 리팩터링 후 기존 PR 열기/업데이트/닫기 흐름 동일한지 확인
2. **Feature 1:** 드래프트 PR 열기 → 리뷰 없음 → "Ready for review" → 리뷰 실행
3. **Feature 2:** GitHub App Settings에서 레포 추가/제거 → DB `is_active` 변경 확인
4. **Feature 3:** PR에 `/re-review` 코멘트 → 리뷰 재실행; 60초 이내 재시도 → 쿨다운 코멘트
5. **Feature 4:** `wip` 라벨 추가 → 스킵 코멘트; 라벨 제거 → 리뷰 실행
