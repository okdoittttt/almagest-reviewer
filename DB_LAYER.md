# PostgreSQL + Async ORM Layer

LangGraph 리뷰 결과를 메모리에만 올리던 구조에서,
PostgreSQL에 영속 저장하는 레이어를 추가한 작업 기록입니다.

---

## 왜 DB가 필요했나

기존에는 `run_review()` 완료 후 결과가 모두 사라졌습니다.
Skills, Multi-repo, PR Triage, Follow-up 기능을 확장하려면 **리뷰 이력과 저장소 정보를 유지**해야 합니다.

---

## 스택

| 역할 | 기술 |
|------|------|
| DB | PostgreSQL 16 (Docker) |
| ORM | SQLAlchemy 2.0 async |
| 드라이버 | asyncpg |
| 마이그레이션 | Alembic |

---

## 스키마

총 5개 테이블. FK는 위→아래 방향으로 CASCADE DELETE.

```
repositories
    └── skills               (저장소별 리뷰 스킬 설정)
    └── pull_requests
            └── reviews      (커밋 SHA 기준 리뷰 스냅샷)
                    └── review_comments
```

### repositories

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | |
| github_repo_id | BIGINT UNIQUE | payload["repository"]["id"] |
| owner | VARCHAR(255) | |
| name | VARCHAR(255) | |
| installation_id | VARCHAR(255) | GitHub App Installation ID |
| is_active | BOOLEAN | 기본 true |

### skills

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | |
| repository_id | BIGINT FK | |
| name | VARCHAR(255) | |
| description | TEXT | |
| criteria | JSONB | 리뷰 기준 (focus_areas 등) |
| is_enabled | BOOLEAN | |

### pull_requests

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | |
| repository_id | BIGINT FK | |
| github_pr_id | BIGINT | payload["pull_request"]["id"] |
| pr_number | INT | 저장소 내 PR 번호 |
| title | VARCHAR(1000) | |
| author_login | VARCHAR(255) | |
| head_sha | VARCHAR(40) | 최신 커밋 SHA (synchronize마다 갱신) |
| base_branch / head_branch | VARCHAR(255) | |
| state | VARCHAR(50) | open / closed / merged |
| risk_level | VARCHAR(20) | LOW / MEDIUM / HIGH |
| triage_priority | INT | nullable, PR Triage 기능용 |

### reviews

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | |
| pull_request_id | BIGINT FK | |
| head_sha | VARCHAR(40) | 어떤 커밋을 리뷰했는지 |
| risk_level / risk_score | VARCHAR / FLOAT | |
| pr_intent | JSONB | 의도 분석 결과 |
| risk_assessment | JSONB | 위험도 평가 결과 |
| file_reviews | JSONB[] | 파일별 리뷰 목록 |
| final_review | TEXT | 최종 리뷰 마크다운 |
| review_decision | VARCHAR(50) | APPROVE / REQUEST_CHANGES / COMMENT |
| retry_count | INT | 재시도 횟수 |
| errors | JSONB[] | 처리 중 에러 목록 |

> 같은 PR이라도 `synchronize` 이벤트(코드 push)마다 새 row가 추가됩니다.
> head_sha로 어떤 커밋을 리뷰했는지 추적할 수 있습니다.

### review_comments

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | |
| review_id | BIGINT FK | |
| filename | VARCHAR(1000) | |
| comment_type | VARCHAR(50) | issue / suggestion |
| body | TEXT | |
| is_addressed | BOOLEAN | Follow-up 추적용 |
| addressed_at | TIMESTAMPTZ | |

---

## 추가된 파일

```
app/database/
├── __init__.py              # engine, async_session_factory, Base, get_db 재export
├── base.py                  # DeclarativeBase + TimestampMixin
├── engine.py                # create_async_engine, get_db (FastAPI Depends용)
└── models/
    ├── __init__.py          # 모든 모델 import (Alembic autogenerate용)
    ├── repository.py
    ├── skill.py
    ├── pull_request.py
    ├── review.py
    └── review_comment.py

app/services/
└── review_service.py        # persist_review_result() 진입점

alembic/
├── env.py                   # async 엔진 연동, settings에서 DB URL 주입
├── script.py.mako
└── versions/
    └── 0001_initial_schema.py

alembic.ini
entrypoint.sh                # alembic upgrade head → uvicorn 실행
```

---

## 수정된 파일

### `docker-compose.yaml`

- `db` 서비스 추가 (postgres:16-alpine)
- healthcheck (`pg_isready`) 추가
- `app`에 `depends_on: db: condition: service_healthy` 추가
- `postgres_data` named volume 추가

### `requirements.txt`

```
sqlalchemy[asyncio]>=2.0.0,<3.0.0
asyncpg>=0.29.0,<1.0.0
alembic>=1.13.0,<2.0.0
```

### `app/config.py`

```python
database_url: str = "postgresql+asyncpg://almagest:almagest@db:5432/almagest_reviewer"
```

### `main.py`

- `Depends(get_db)` → webhook 핸들러에 `AsyncSession` 주입
- `run_review()` 완료 후 `persist_review_result()` 호출
- 순서: `run_review` → `persist_review_result` → `create_pr_comment`

### `Dockerfile`

```dockerfile
CMD ["sh", "entrypoint.sh"]
```

> `CMD ["./entrypoint.sh"]` 대신 `sh`를 명시.
> `volumes: .:/app` 마운트 시 호스트 파일의 실행 비트가 없어 permission denied가 발생했기 때문.

---

## 요청 흐름

```
GitHub Webhook
    ↓
FastAPI → get_db() → AsyncSession 생성
    ↓
run_review() — LangGraph 실행 (DB 없음, 순수 로직)
    ↓
persist_review_result(session, ...)
    ├─ upsert repositories
    ├─ upsert pull_requests
    ├─ insert reviews
    └─ insert review_comments
    ↓
create_pr_comment() → GitHub 코멘트 게시
    ↓
JSONResponse → session.commit()
예외 발생 시 → session.rollback()
```

---

## 검증 쿼리

```sql
SELECT * FROM repositories;
SELECT * FROM pull_requests ORDER BY created_at DESC;
SELECT * FROM reviews ORDER BY created_at DESC;
SELECT * FROM review_comments WHERE review_id = <id>;
```

같은 PR에 코드를 push(synchronize)하면 `reviews` 테이블에 head_sha가 다른 row가 추가되는지 확인.
