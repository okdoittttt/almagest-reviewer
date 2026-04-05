#!/bin/bash
# deploy.sh — 배포 및 마이그레이션 관리 스크립트
set -euo pipefail

# ── 색상 출력 ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
header()  { echo -e "\n${BOLD}${CYAN}=== $* ===${NC}"; }

# ── 환경 선택 (dev | prod, 기본값: prod) ──────────────────────────────────────
ENV_MODE="prod"
if [[ "${1:-}" == "dev" || "${1:-}" == "prod" ]]; then
    ENV_MODE="$1"
    shift
fi

if [[ "$ENV_MODE" == "dev" ]]; then
    COMPOSE_CMD="docker compose -f docker-compose.dev.yml"
    ENV_LABEL="로컬 개발(dev)"
else
    COMPOSE_CMD="docker compose"   # docker-compose.yml (운영)
    ENV_LABEL="운영(prod)"
fi

# ── 마이그레이션 현황 조회 ────────────────────────────────────────────────────
migration_status() {
    header "마이그레이션 현황 [$ENV_LABEL]"

    if ! $COMPOSE_CMD ps db --status running --quiet 2>/dev/null | grep -q .; then
        warn "DB 컨테이너가 실행 중이지 않습니다. 먼저 'deploy.sh ${ENV_MODE} up' 또는 'deploy.sh ${ENV_MODE} db'를 실행하세요."
        exit 1
    fi

    info "적용된 마이그레이션:"
    $COMPOSE_CMD run --rm --no-deps \
        -e DATABASE_URL="postgresql+asyncpg://almagest:almagest@db:5432/almagest_reviewer" \
        app alembic history --indicate-current 2>/dev/null \
        | sed 's/^/  /'

    echo ""
    info "현재 버전:"
    CURRENT=$($COMPOSE_CMD run --rm --no-deps \
        -e DATABASE_URL="postgresql+asyncpg://almagest:almagest@db:5432/almagest_reviewer" \
        app alembic current 2>/dev/null | grep -v "^$" || echo "  (없음 — 마이그레이션 미적용)")
    echo -e "  ${BOLD}${CURRENT}${NC}"

    echo ""
    info "미적용 마이그레이션 확인:"
    PENDING=$($COMPOSE_CMD run --rm --no-deps \
        -e DATABASE_URL="postgresql+asyncpg://almagest:almagest@db:5432/almagest_reviewer" \
        app alembic heads 2>/dev/null)
    CURRENT_REV=$($COMPOSE_CMD run --rm --no-deps \
        -e DATABASE_URL="postgresql+asyncpg://almagest:almagest@db:5432/almagest_reviewer" \
        app alembic current 2>/dev/null | awk '{print $1}')

    if echo "$PENDING" | grep -q "$CURRENT_REV"; then
        success "최신 상태입니다."
    else
        warn "적용되지 않은 마이그레이션이 있습니다."
        warn "  최신 head: $PENDING"
        warn "  현재 버전: ${CURRENT_REV:-없음}"
    fi
}

# ── 마이그레이션 실행 ─────────────────────────────────────────────────────────
run_migrate() {
    header "마이그레이션 실행 [$ENV_LABEL]"

    if ! $COMPOSE_CMD ps db --status running --quiet 2>/dev/null | grep -q .; then
        error "DB 컨테이너가 실행 중이지 않습니다."
        exit 1
    fi

    info "마이그레이션 전 버전:"
    $COMPOSE_CMD run --rm --no-deps \
        -e DATABASE_URL="postgresql+asyncpg://almagest:almagest@db:5432/almagest_reviewer" \
        app alembic current 2>/dev/null | sed 's/^/  /' || echo "  (없음)"

    info "alembic upgrade head 실행 중..."
    $COMPOSE_CMD run --rm --no-deps \
        -e DATABASE_URL="postgresql+asyncpg://almagest:almagest@db:5432/almagest_reviewer" \
        app alembic upgrade head

    echo ""
    info "마이그레이션 후 버전:"
    $COMPOSE_CMD run --rm --no-deps \
        -e DATABASE_URL="postgresql+asyncpg://almagest:almagest@db:5432/almagest_reviewer" \
        app alembic current 2>/dev/null | sed 's/^/  /'

    success "마이그레이션 완료."
}

# ── 배포 (전체) ───────────────────────────────────────────────────────────────
deploy() {
    header "배포 시작 [$ENV_LABEL]"

    info "1/4  기존 컨테이너 종료..."
    $COMPOSE_CMD down --remove-orphans

    info "2/4  이미지 빌드..."
    $COMPOSE_CMD build --no-cache

    info "3/4  DB 컨테이너 기동 및 헬스체크 대기..."
    $COMPOSE_CMD up -d db
    echo -n "  DB 준비 대기 중"
    until $COMPOSE_CMD ps db --status running --quiet 2>/dev/null | grep -q . && \
          $COMPOSE_CMD exec db pg_isready -U almagest -d almagest_reviewer -q 2>/dev/null; do
        echo -n "."
        sleep 2
    done
    echo " 완료"

    info "4/4  마이그레이션 실행..."
    run_migrate

    info "앱 및 프론트엔드 컨테이너 기동..."
    $COMPOSE_CMD up -d app web

    echo ""
    success "배포 완료."
    migration_status
}

# ── 컨테이너 기동만 (빌드 없음) ───────────────────────────────────────────────
up() {
    header "컨테이너 기동 [$ENV_LABEL]"
    $COMPOSE_CMD up -d
    success "기동 완료."
}

# ── 컨테이너 종료 ─────────────────────────────────────────────────────────────
down() {
    header "컨테이너 종료 [$ENV_LABEL]"
    $COMPOSE_CMD down
    success "종료 완료."
}

# ── DB만 기동 ─────────────────────────────────────────────────────────────────
db_up() {
    header "DB 컨테이너 기동 [$ENV_LABEL]"
    $COMPOSE_CMD up -d db
    echo -n "  DB 준비 대기 중"
    until $COMPOSE_CMD exec db pg_isready -U almagest -d almagest_reviewer -q 2>/dev/null; do
        echo -n "."
        sleep 2
    done
    echo " 완료"
    success "DB 준비됐습니다."
}

# ── 로그 확인 ─────────────────────────────────────────────────────────────────
logs() {
    local service="${1:-app}"
    $COMPOSE_CMD logs -f "$service"
}

# ── 도움말 ────────────────────────────────────────────────────────────────────
usage() {
    echo -e "${BOLD}사용법:${NC} ./deploy.sh [dev|prod] <명령어>"
    echo ""
    echo -e "${BOLD}환경:${NC}"
    echo "  prod      운영 환경 (기본값) — docker-compose.yml, production 빌드"
    echo "  dev       로컬 개발 환경 — docker-compose.dev.yml, hot-reload 활성화"
    echo ""
    echo -e "${BOLD}명령어:${NC}"
    echo "  deploy    이미지 빌드 → 마이그레이션 → 전체 기동 (전체 배포)"
    echo "  up        컨테이너 기동 (빌드 없음)"
    echo "  down      컨테이너 종료"
    echo "  db        DB 컨테이너만 기동"
    echo "  migrate   마이그레이션 실행 (alembic upgrade head)"
    echo "  status    마이그레이션 현황 및 버전 확인"
    echo "  logs      로그 확인 (기본: app, 예: ./deploy.sh logs web)"
    echo ""
    echo -e "${BOLD}예시:${NC}"
    echo "  ./deploy.sh deploy              # 운영 전체 배포"
    echo "  ./deploy.sh dev up              # 로컬 개발 환경 기동"
    echo "  ./deploy.sh dev down            # 로컬 개발 환경 종료"
    echo "  ./deploy.sh dev logs web        # 로컬 프론트엔드 로그"
    echo "  ./deploy.sh status              # 운영 마이그레이션 버전 확인"
    echo "  ./deploy.sh dev migrate         # 로컬 마이그레이션 실행"
}

# ── 진입점 ────────────────────────────────────────────────────────────────────
CMD="${1:-}"

case "$CMD" in
    deploy)  deploy ;;
    up)      up ;;
    down)    down ;;
    db)      db_up ;;
    migrate) run_migrate ;;
    status)  migration_status ;;
    logs)    logs "${2:-app}" ;;
    *)       usage ;;
esac
