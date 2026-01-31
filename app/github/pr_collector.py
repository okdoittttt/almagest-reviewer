"""
Pull Request 데이터 수집 모듈
"""
from typing import Optional
from loguru import logger

from app.github.client import GitHubClient
from app.models import PRData, FileChange, CommitInfo, Author


class PRDataCollector:
    """
    Pull Request의 모든 데이터를 수집하고 구조화된 PRData 객체로 변환
    """

    def __init__(self, github_client: GitHubClient):
        self.client = github_client

    async def collect_pr_data(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        pull_number: int,
        include_commits: bool = True
    ) -> PRData:
        """
        PR의 모든 데이터를 수집하여 PRData 객체로 반환

        Args:
            installation_id: GitHub App Installation ID
            repo_owner: 리포지토리 소유자
            repo_name: 리포지토리 이름
            pull_number: PR 번호
            include_commits: 커밋 목록 포함 여부 (기본: True)

        Returns:
            수집된 PR 데이터

        Raises:
            httpx.HTTPStatusError: GitHub API 호출 실패 시
        """
        logger.info(f"PR 데이터 수집 시작: {repo_owner}/{repo_name}#{pull_number}")

        # 1. PR 상세 정보 조회
        pr_details = await self.client.get_pr_details(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pull_number
        )

        # 2. 변경된 파일 목록 조회
        files_data = await self.client.get_pr_files(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pull_number
        )

        # 3. 커밋 목록 조회 (옵션)
        commits_data = []
        if include_commits:
            commits_data = await self.client.get_pr_commits(
                installation_id=installation_id,
                repo_owner=repo_owner,
                repo_name=repo_name,
                pull_number=pull_number
            )

        # 4. 데이터 변환
        pr_data = self._convert_to_pr_data(
            pr_details=pr_details,
            files_data=files_data,
            commits_data=commits_data,
            repo_owner=repo_owner,
            repo_name=repo_name
        )

        logger.info(
            f"PR 데이터 수집 완료: {pr_data.changed_files_count}개 파일, "
            f"{pr_data.commits_count}개 커밋, "
            f"+{pr_data.total_additions}/-{pr_data.total_deletions}"
        )

        return pr_data

    def _convert_to_pr_data(
        self,
        pr_details: dict,
        files_data: list[dict],
        commits_data: list[dict],
        repo_owner: str,
        repo_name: str
    ) -> PRData:
        """
        GitHub API 응답을 PRData 객체로 변환

        Args:
            pr_details: PR 상세 정보
            files_data: 변경된 파일 목록
            commits_data: 커밋 목록
            repo_owner: 리포지토리 소유자
            repo_name: 리포지토리 이름

        Returns:
            변환된 PRData 객체
        """
        # Author 변환
        author = Author(
            login=pr_details["user"]["login"],
            id=pr_details["user"]["id"],
            avatar_url=pr_details["user"].get("avatar_url")
        )

        # FileChange 목록 변환
        files = [self._convert_to_file_change(f) for f in files_data]

        # CommitInfo 목록 변환
        commits = [self._convert_to_commit_info(c) for c in commits_data]

        # 통계 계산
        total_additions = sum(f.additions for f in files)
        total_deletions = sum(f.deletions for f in files)
        total_changes = sum(f.changes for f in files)

        return PRData(
            pr_number=pr_details["number"],
            title=pr_details["title"],
            body=pr_details.get("body"),
            state=pr_details["state"],
            author=author,
            base_branch=pr_details["base"]["ref"],
            head_branch=pr_details["head"]["ref"],
            base_sha=pr_details["base"]["sha"],
            head_sha=pr_details["head"]["sha"],
            repo_owner=repo_owner,
            repo_name=repo_name,
            files=files,
            commits=commits,
            total_additions=total_additions,
            total_deletions=total_deletions,
            total_changes=total_changes,
            changed_files_count=len(files),
            commits_count=len(commits),
            html_url=pr_details.get("html_url"),
            diff_url=pr_details.get("diff_url")
        )

    def _convert_to_file_change(self, file_data: dict) -> FileChange:
        """
        GitHub API의 파일 데이터를 FileChange 객체로 변환

        Args:
            file_data: GitHub API 파일 데이터

        Returns:
            변환된 FileChange 객체
        """
        return FileChange(
            filename=file_data["filename"],
            status=file_data["status"],
            additions=file_data.get("additions", 0),
            deletions=file_data.get("deletions", 0),
            changes=file_data.get("changes", 0),
            patch=file_data.get("patch"),
            blob_url=file_data.get("blob_url"),
            previous_filename=file_data.get("previous_filename")
        )

    def _convert_to_commit_info(self, commit_data: dict) -> CommitInfo:
        """
        GitHub API의 커밋 데이터를 CommitInfo 객체로 변환

        Args:
            commit_data: GitHub API 커밋 데이터

        Returns:
            변환된 CommitInfo 객체
        """
        # 커밋 작성자 정보
        author_data = commit_data.get("author") or commit_data["commit"]["author"]

        # author_data가 None이거나 필수 필드가 없는 경우 처리
        if isinstance(author_data, dict) and "login" in author_data:
            author = Author(
                login=author_data["login"],
                id=author_data.get("id", 0),
                avatar_url=author_data.get("avatar_url")
            )
        else:
            # commit author로 폴백 (이메일 기반)
            commit_author = commit_data["commit"]["author"]
            author = Author(
                login=commit_author.get("name", "unknown"),
                id=0,
                avatar_url=None
            )

        return CommitInfo(
            sha=commit_data["sha"],
            message=commit_data["commit"]["message"],
            author=author,
            url=commit_data.get("html_url"),
            committed_at=commit_data["commit"]["author"].get("date")
        )

    async def get_file_diff(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        pull_number: int,
        filename: str
    ) -> Optional[str]:
        """
        특정 파일의 diff만 가져오기

        Args:
            installation_id: GitHub App Installation ID
            repo_owner: 리포지토리 소유자
            repo_name: 리포지토리 이름
            pull_number: PR 번호
            filename: 파일명

        Returns:
            파일의 diff (patch), 없으면 None
        """
        files_data = await self.client.get_pr_files(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pull_number
        )

        for file_data in files_data:
            if file_data["filename"] == filename:
                return file_data.get("patch")

        logger.warning(f"파일을 찾을 수 없습니다: {filename}")
        return None
