"""GitHub App 인증 방식을 사용하는 GitHub API 클라이언트."""
from datetime import datetime, timedelta
from typing import Any

import httpx
from loguru import logger

from app.config import settings
from app.auth import generate_jwt


class GitHubClient:
    """GitHub App 인증을 자동으로 처리하는 GitHub API 클라이언트.

    JWT 생성과 Installation Access Token 발급 및 관리를 내부에서 자동으로 처리한다.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.app_id = settings.github_app_id
        self.private_key = settings.read_private_key()
        self._installation_token: str | None = None
        self._token_expires_at: datetime | None = None

    def _get_jwt(self) -> str:
        """GitHub App 인증에 사용되는 JWT 토큰을 생성한다.

        Returns:
            JWT 토큰 문자열
        """
        return generate_jwt(self.app_id, self.private_key)

    async def get_installation_token(self, installation_id: str) -> str:
        """JWT를 사용해 Installation Access Token을 발급받는다.

        발급된 토큰은 만료될 때까지(최대 1시간) 캐시하여 재사용한다.

        Args:
            installation_id: GitHub App의 Installation ID

        Returns:
            Installation Access Token 문자열

        Raises:
            httpx.HTTPStatusError: GitHub API 호출 결과 에러가 발생한 경우
        """
        # 캐시된 토큰이 있고 아직 유효하다면 재사용
        if self._installation_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                logger.debug("캐시된 installation token을 재사용합니다")
                return self._installation_token

        # 새로운 JWT 생성
        jwt_token = self._get_jwt()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            # 토큰 캐싱
            self._installation_token = data["token"]
            # Installation Access Token은 최대 1시간 유효
            self._token_expires_at = datetime.now() + timedelta(hours=1)

            logger.info(f"Installation {installation_id}에 대한 새로운 토큰을 발급받았습니다")
            return self._installation_token

    async def create_pr_comment(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        pull_number: int,
        comment_body: str
    ) -> dict[str, Any]:
        """Pull Request에 코멘트를 작성한다.

        Args:
            installation_id: GitHub App의 Installation ID
            repo_owner: 저장소 소유자 (사용자 또는 조직)
            repo_name: 저장소 이름
            pull_number: Pull Request 번호
            comment_body: 코멘트 내용 (Markdown 지원)

        Returns:
            생성된 코멘트 정보가 담긴 API 응답 데이터

        Raises:
            httpx.HTTPStatusError: GitHub API 호출 결과 에러가 발생한 경우
        """
        token = await self.get_installation_token(installation_id)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}/issues/{pull_number}/comments",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                json={"body": comment_body},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"{repo_owner}/{repo_name}의 PR #{pull_number}에 코멘트를 생성했습니다")
            return data

    async def get_pr_files(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        pull_number: int
    ) -> list[dict[str, Any]]:
        """Pull Request에서 변경된 파일 목록을 조회한다.

        Args:
            installation_id: GitHub App의 Installation ID
            repo_owner: 저장소 소유자
            repo_name: 저장소 이름
            pull_number: Pull Request 번호

        Returns:
            변경된 파일 목록 (patch, additions, deletions 등의 정보 포함)

        Raises:
            httpx.HTTPStatusError: GitHub API 호출 결과 에러가 발생한 경우
        """
        token = await self.get_installation_token(installation_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}/pulls/{pull_number}/files",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"PR #{pull_number}에서 {len(data)}개의 변경 파일을 조회했습니다")
            return data

    async def get_file_content(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        file_path: str,
        ref: str = "main"
    ) -> str:
        """저장소 내 특정 파일의 내용을 조회한다.

        Args:
            installation_id: GitHub App의 Installation ID
            repo_owner: 저장소 소유자
            repo_name: 저장소 이름
            file_path: 저장소 내 파일 경로
            ref: Git 참조 (브랜치, 태그 또는 커밋 SHA)

        Returns:
            파일 내용을 문자열 형태로 반환

        Raises:
            httpx.HTTPStatusError: GitHub API 호출 결과 에러가 발생한 경우
        """
        token = await self.get_installation_token(installation_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}/contents/{file_path}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.raw+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                params={"ref": ref},
                timeout=10.0
            )
            response.raise_for_status()

            logger.debug(f"{repo_owner}/{repo_name}의 {file_path} 파일 내용을 조회했습니다")
            return response.text

    async def get_pr_commits(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        pull_number: int
    ) -> list[dict[str, Any]]:
        """Pull Request의 커밋 목록을 조회한다.

        Args:
            installation_id: GitHub App의 Installation ID
            repo_owner: 저장소 소유자
            repo_name: 저장소 이름
            pull_number: Pull Request 번호

        Returns:
            커밋 목록 (SHA, 메시지, 작성자 등의 정보 포함)

        Raises:
            httpx.HTTPStatusError: GitHub API 호출 결과 에러가 발생한 경우
        """
        token = await self.get_installation_token(installation_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}/pulls/{pull_number}/commits",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"PR #{pull_number}에서 {len(data)}개의 커밋을 조회했습니다")
            return data

    async def list_prs(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        state: str = "all",
        per_page: int = 100,
    ) -> list[dict[str, Any]]:
        """저장소의 Pull Request 목록을 조회한다.

        Args:
            installation_id: GitHub App의 Installation ID
            repo_owner: 저장소 소유자
            repo_name: 저장소 이름
            state: PR 상태 필터 ("open", "closed", "all")
            per_page: 페이지당 결과 수 (최대 100)

        Returns:
            PR 목록 (number, state, merged_at 등의 정보 포함)

        Raises:
            httpx.HTTPStatusError: GitHub API 호출 결과 에러가 발생한 경우
        """
        token = await self.get_installation_token(installation_id)
        results: list[dict[str, Any]] = []
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}/pulls",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"
                    },
                    params={"state": state, "per_page": per_page, "page": page},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                if not data:
                    break
                results.extend(data)
                if len(data) < per_page:
                    break
                page += 1

        logger.info(f"{repo_owner}/{repo_name}에서 PR {len(results)}개를 조회했습니다 (state={state})")
        return results

    async def merge_pull_request(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        pull_number: int,
        merge_method: str = "squash",
    ) -> dict[str, Any]:
        """Pull Request를 병합한다.

        Args:
            installation_id: GitHub App의 Installation ID
            repo_owner: 저장소 소유자
            repo_name: 저장소 이름
            pull_number: Pull Request 번호
            merge_method: 병합 방식 ("squash", "rebase", "merge")

        Returns:
            병합 결과 (sha, merged, message)

        Raises:
            httpx.HTTPStatusError: 병합 불가 상태(405)나 충돌(409) 등
        """
        token = await self.get_installation_token(installation_id)

        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}/pulls/{pull_number}/merge",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                json={"merge_method": merge_method},
                timeout=15.0
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"{repo_owner}/{repo_name} PR #{pull_number}을 {merge_method} 방식으로 병합했습니다")
            return data

    async def create_pr_review_reply(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        pull_number: int,
        body: str,
    ) -> dict[str, Any]:
        """Pull Request에 답글 코멘트를 작성한다.

        Args:
            installation_id: GitHub App의 Installation ID
            repo_owner: 저장소 소유자
            repo_name: 저장소 이름
            pull_number: Pull Request 번호
            body: 코멘트 내용

        Returns:
            생성된 코멘트 정보

        Raises:
            httpx.HTTPStatusError: GitHub API 호출 결과 에러가 발생한 경우
        """
        return await self.create_pr_comment(
            installation_id=installation_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pull_number=pull_number,
            comment_body=body,
        )

    async def get_pr_details(
        self,
        installation_id: str,
        repo_owner: str,
        repo_name: str,
        pull_number: int
    ) -> dict[str, Any]:
        """Pull Request의 상세 정보를 조회한다.

        Args:
            installation_id: GitHub App의 Installation ID
            repo_owner: 저장소 소유자
            repo_name: 저장소 이름
            pull_number: Pull Request 번호

        Returns:
            PR 상세 정보 (제목, 본문, 브랜치, 작성자 등)

        Raises:
            httpx.HTTPStatusError: GitHub API 호출 결과 에러가 발생한 경우
        """
        token = await self.get_installation_token(installation_id)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{repo_owner}/{repo_name}/pulls/{pull_number}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"PR #{pull_number}의 상세 정보를 조회했습니다")
            return data
