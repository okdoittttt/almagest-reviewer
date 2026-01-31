"""
PR 데이터 수집 테스트

실제 GitHub API를 호출하므로, 유효한 PR이 필요합니다.
테스트 전에 GitHub 리포지토리에 테스트용 PR을 생성해주세요.
"""
import asyncio
from app.config import settings
from app.github import GitHubClient, PRDataCollector


async def test_pr_data_collection():
    """
    실제 PR 데이터 수집 테스트

    테스트하기 전에 다음을 설정하세요:
    1. 실제 GitHub 리포지토리에 테스트용 PR 생성
    2. 아래 변수들을 실제 값으로 변경
    """
    print("=== PR 데이터 수집 테스트 ===\n")

    # TODO: 실제 값으로 변경하세요
    TEST_REPO_OWNER = "your-github-username"  # 예: "okdoittttt"
    TEST_REPO_NAME = "your-repo-name"         # 예: "test-repo"
    TEST_PR_NUMBER = 1                        # 예: 1

    print("⚠️  테스트 설정:")
    print(f"  리포지토리: {TEST_REPO_OWNER}/{TEST_REPO_NAME}")
    print(f"  PR 번호: #{TEST_PR_NUMBER}")
    print(f"  Installation ID: {settings.github_installation_id}\n")

    if TEST_REPO_OWNER == "your-github-username":
        print("❌ 테스트를 실행하려면 먼저 위 TODO 섹션의 값을 실제 값으로 변경하세요!")
        return

    # GitHub 클라이언트 및 PR 수집기 초기화
    github_client = GitHubClient()
    pr_collector = PRDataCollector(github_client)

    try:
        # PR 데이터 수집
        print("📥 PR 데이터 수집 중...\n")
        pr_data = await pr_collector.collect_pr_data(
            installation_id=settings.github_installation_id,
            repo_owner=TEST_REPO_OWNER,
            repo_name=TEST_REPO_NAME,
            pull_number=TEST_PR_NUMBER,
            include_commits=True
        )

        # 결과 출력
        print("✅ PR 데이터 수집 성공!\n")
        print("=" * 60)
        print(f"PR #{pr_data.pr_number}: {pr_data.title}")
        print("=" * 60)

        print(f"\n📝 기본 정보:")
        print(f"  작성자: @{pr_data.author.login}")
        print(f"  상태: {pr_data.state}")
        print(f"  브랜치: {pr_data.head_branch} → {pr_data.base_branch}")
        print(f"  URL: {pr_data.html_url}")

        if pr_data.body:
            print(f"\n📄 본문:")
            print(f"  {pr_data.body[:200]}..." if len(pr_data.body) > 200 else f"  {pr_data.body}")

        print(f"\n📊 통계:")
        print(f"  파일: {pr_data.changed_files_count}개")
        print(f"  커밋: {pr_data.commits_count}개")
        print(f"  추가: +{pr_data.total_additions} 줄")
        print(f"  삭제: -{pr_data.total_deletions} 줄")
        print(f"  변경: {pr_data.total_changes} 줄")

        if pr_data.has_files:
            print(f"\n📁 변경된 파일 ({pr_data.changed_files_count}개):")
            for i, file in enumerate(pr_data.files[:5], 1):
                status_emoji = "✨" if file.is_new_file else "🗑️" if file.is_deleted_file else "📝"
                print(f"  {i}. {status_emoji} {file.filename}")
                print(f"     상태: {file.status} | +{file.additions}/-{file.deletions}")
                if file.patch:
                    patch_lines = len(file.patch.split('\n'))
                    print(f"     Diff: {patch_lines} 줄")

            if pr_data.changed_files_count > 5:
                print(f"  ... 외 {pr_data.changed_files_count - 5}개 파일")

        if pr_data.has_commits:
            print(f"\n💾 커밋 ({pr_data.commits_count}개):")
            for i, commit in enumerate(pr_data.commits[:3], 1):
                message_first_line = commit.message.split('\n')[0]
                print(f"  {i}. {commit.sha[:7]} - {message_first_line}")
                print(f"     작성자: @{commit.author.login}")

            if pr_data.commits_count > 3:
                print(f"  ... 외 {pr_data.commits_count - 3}개 커밋")

        # 유틸리티 메서드 테스트
        print(f"\n🔧 유틸리티 메서드 테스트:")
        py_files = pr_data.get_files_by_extension(".py")
        print(f"  Python 파일: {len(py_files)}개")

        modified_only = pr_data.get_modified_files_only()
        print(f"  수정된 파일만: {len(modified_only)}개")

        if pr_data.files:
            first_file = pr_data.get_file_by_name(pr_data.files[0].filename)
            print(f"  파일 검색: {first_file.filename if first_file else 'None'}")

        print("\n" + "=" * 60)
        print("🎉 테스트 완료!")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        print(f"에러 타입: {type(e).__name__}")
        import traceback
        traceback.print_exc()


async def test_pr_data_model():
    """PR 데이터 모델 테스트"""
    print("\n=== PR 데이터 모델 테스트 ===\n")

    from app.models import PRData, FileChange, Author

    # 샘플 데이터 생성
    author = Author(login="testuser", id=123, avatar_url="https://github.com/testuser.png")

    files = [
        FileChange(
            filename="src/app.py",
            status="modified",
            additions=10,
            deletions=5,
            changes=15,
            patch="@@ -1,5 +1,10 @@\n-old line\n+new line"
        ),
        FileChange(
            filename="tests/test_app.py",
            status="added",
            additions=50,
            deletions=0,
            changes=50
        )
    ]

    pr_data = PRData(
        pr_number=42,
        title="Test PR",
        body="This is a test PR",
        state="open",
        author=author,
        base_branch="main",
        head_branch="feature/test",
        base_sha="abc123",
        head_sha="def456",
        repo_owner="testorg",
        repo_name="testrepo",
        files=files,
        total_additions=60,
        total_deletions=5,
        total_changes=65,
        changed_files_count=2,
        commits_count=3
    )

    print(f"PR 데이터 생성: #{pr_data.pr_number} - {pr_data.title}")
    print(f"파일 수: {pr_data.changed_files_count}")
    print(f"has_files: {pr_data.has_files}")
    print(f"Python 파일: {len(pr_data.get_files_by_extension('.py'))}개")
    print(f"수정된 파일: {len(pr_data.get_modified_files_only())}개")

    # JSON 직렬화 테스트
    import json
    json_str = pr_data.model_dump_json(indent=2)
    print(f"\nJSON 직렬화 성공 (길이: {len(json_str)} 바이트)")

    print("\n✅ 모델 테스트 통과!")


if __name__ == "__main__":
    print("🚀 PR 데이터 수집 테스트 시작\n")
    asyncio.run(test_pr_data_model())
    asyncio.run(test_pr_data_collection())
