"""리뷰 대상에서 제외할 파일을 판별하는 범용 필터 모듈.

자동 생성 파일, 의존성 잠금 파일, 빌드 산출물 등 코드 리뷰 가치가 낮은
파일을 여러 언어·프레임워크에 걸쳐 일관되게 식별합니다.
"""
import re

# ---------------------------------------------------------------------------
# 정확한 파일명 매칭 (베이스네임 기준, 대소문자 구분)
# ---------------------------------------------------------------------------
_SKIP_EXACT: frozenset[str] = frozenset({
    # JavaScript / Node.js
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "npm-shrinkwrap.json",
    # Python
    "poetry.lock",
    "Pipfile.lock",
    "uv.lock",
    "pdm.lock",
    # Ruby
    "Gemfile.lock",
    # Go
    "go.sum",
    # PHP
    "composer.lock",
    # Rust
    "Cargo.lock",
    # .NET / NuGet
    "packages.lock.json",
    # Dart / Flutter
    "pubspec.lock",
    # OS 메타데이터
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
})

# ---------------------------------------------------------------------------
# 경로 접두어 매칭 (디렉터리 단위, / 포함)
# 파일 경로가 해당 접두어로 시작하거나 경로 중간에 포함되면 제외
# ---------------------------------------------------------------------------
_SKIP_PATH_SEGMENTS: tuple[str, ...] = (
    # 의존성 디렉터리
    "node_modules/",
    "vendor/",
    "third_party/",
    "bower_components/",
    # Python 가상환경
    "venv/",
    ".venv/",
    "env/",
    ".env/",
    "virtualenv/",
    # 빌드 산출물
    "dist/",
    "build/",
    ".build/",
    "out/",
    "target/",          # Rust / Java / Kotlin
    "bin/",
    "obj/",             # .NET
    # 프레임워크 캐시
    ".next/",
    ".nuxt/",
    ".svelte-kit/",
    ".output/",         # Nuxt 3
    ".cache/",
    # Python 캐시
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    # Java 빌드
    ".gradle/",
    ".m2/",
    # IDE
    ".idea/",
    ".vscode/",
    # 커버리지 리포트
    "htmlcov/",
    "coverage/",
    ".coverage/",
    # 문서 빌드
    "site/",
    "docs/_build/",
    "docs/build/",
)

# ---------------------------------------------------------------------------
# 파일 접미사 매칭 (경로 전체 끝부분)
# ---------------------------------------------------------------------------
_SKIP_SUFFIXES: tuple[str, ...] = (
    # 컴파일된 Python
    ".pyc", ".pyo", ".pyd",
    # 소스맵
    ".js.map", ".css.map", ".ts.map",
    # 축소(minified) 파일
    ".min.js", ".min.css",
    # Protobuf 자동 생성
    "_pb2.py", "_pb2_grpc.py", ".pb.go", ".pb.swift",
    # gRPC 자동 생성
    "_grpc.pb.go",
    # GraphQL 자동 생성
    ".generated.ts", ".generated.tsx", ".generated.js",
    # Flutter / Dart 자동 생성
    ".g.dart", ".freezed.dart", ".gr.dart",
    # Kotlin / Android 자동 생성
    ".generated.kt",
    # 바이너리 확장자
    ".wasm",
)

# ---------------------------------------------------------------------------
# 베이스네임 정규식 매칭 (복잡한 패턴)
# ---------------------------------------------------------------------------
_SKIP_BASENAME_PATTERNS: tuple[re.Pattern, ...] = (
    # *_generated.*, generated_*
    re.compile(r"(_generated\.|generated_)", re.IGNORECASE),
    # *.gen.*, *_gen.go 등
    re.compile(r"\.(gen|auto)\.", re.IGNORECASE),
    re.compile(r"_gen\.(go|py|ts|java|kt)$", re.IGNORECASE),
    # __generated__* (Relay, GraphQL Codegen)
    re.compile(r"^__generated__", re.IGNORECASE),
    # *.bundle.js
    re.compile(r"\.bundle\.(js|css)$", re.IGNORECASE),
    # swagger / openapi 자동 생성 클라이언트
    re.compile(r"^(swagger|openapi)_?(client|types|models)\.", re.IGNORECASE),
)


def should_skip_file(filename: str) -> tuple[bool, str]:
    """파일이 코드 리뷰 대상에서 제외되어야 하는지 판별합니다.

    lock 파일, 자동 생성 파일, 빌드 산출물, 의존성 디렉터리 내 파일 등
    리뷰 가치가 낮은 파일을 여러 언어·프레임워크에 걸쳐 감지합니다.

    Args:
        filename: 저장소 루트 기준 파일 경로 (예: ``src/generated/types.ts``).

    Returns:
        ``(skip, reason)`` 튜플.
        ``skip``이 True이면 리뷰를 건너뛰어야 하며, ``reason``에 사유가 담깁니다.
    """
    basename = filename.rsplit("/", 1)[-1]

    # 1. 정확한 파일명 매칭
    if basename in _SKIP_EXACT:
        return True, f"lock/metadata file: {basename}"

    # 2. 경로 세그먼트 매칭 (경로 어디에 포함돼도 제외)
    normalized = filename if filename.startswith("/") else "/" + filename
    for segment in _SKIP_PATH_SEGMENTS:
        if ("/" + segment) in normalized or filename.startswith(segment):
            return True, f"excluded directory: {segment.rstrip('/')}"

    # 3. 접미사 매칭
    for suffix in _SKIP_SUFFIXES:
        if filename.endswith(suffix):
            return True, f"generated/compiled suffix: {suffix}"

    # 4. 베이스네임 정규식 매칭
    for pattern in _SKIP_BASENAME_PATTERNS:
        if pattern.search(basename):
            return True, f"generated file pattern: {pattern.pattern}"

    return False, ""
