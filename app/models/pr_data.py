"""Pull Request 데이터 모델."""

from typing import Optional
from pydantic import BaseModel, Field


class Author(BaseModel):
    """작성자 정보.

    Attributes:
        login (str): GitHub 로그인 아이디.
        id (int): GitHub 사용자 ID.
        avatar_url (Optional[str]): 프로필 이미지 URL.
    """

    login: str
    id: int
    avatar_url: Optional[str] = None


class FileChange(BaseModel):
    """변경된 파일 정보.

    Attributes:
        filename (str): 파일 경로.
        status (str): 파일 상태 (added, modified, removed, renamed).
        additions (int): 추가된 라인 수.
        deletions (int): 삭제된 라인 수.
        changes (int): 전체 변경 라인 수.
        patch (Optional[str]): 파일의 diff (unified diff 형식).
        blob_url (Optional[str]): 파일 전체 내용 URL.
        previous_filename (Optional[str]): 이름 변경된 경우 이전 파일명.
    """

    filename: str = Field(..., description="파일 경로")
    status: str = Field(..., description="파일 상태 (added, modified, removed, renamed)")
    additions: int = Field(0, description="추가된 라인 수")
    deletions: int = Field(0, description="삭제된 라인 수")
    changes: int = Field(0, description="전체 변경 라인 수")
    patch: Optional[str] = Field(None, description="파일의 diff (unified diff 형식)")
    blob_url: Optional[str] = Field(None, description="파일 전체 내용 URL")
    previous_filename: Optional[str] = Field(None, description="이름 변경된 경우 이전 파일명")

    @property
    def is_new_file(self) -> bool:
        """새로 추가된 파일인지 확인.

        Returns:
            bool: 파일 상태가 'added'이면 True.
        """
        return self.status == "added"

    @property
    def is_deleted_file(self) -> bool:
        """삭제된 파일인지 확인.

        Returns:
            bool: 파일 상태가 'removed'이면 True.
        """
        return self.status == "removed"

    @property
    def is_renamed_file(self) -> bool:
        """이름이 변경된 파일인지 확인.

        Returns:
            bool: 파일 상태가 'renamed'이면 True.
        """
        return self.status == "renamed"


class CommitInfo(BaseModel):
    """커밋 정보.

    Attributes:
        sha (str): 커밋 SHA.
        message (str): 커밋 메시지.
        author (Author): 커밋 작성자.
        url (Optional[str]): 커밋 URL.
        committed_at (Optional[str]): 커밋 시간.
    """

    sha: str = Field(..., description="커밋 SHA")
    message: str = Field(..., description="커밋 메시지")
    author: Author = Field(..., description="커밋 작성자")
    url: Optional[str] = Field(None, description="커밋 URL")
    committed_at: Optional[str] = Field(None, description="커밋 시간")


class PRData(BaseModel):
    """Pull Request 전체 데이터.

    Attributes:
        pr_number (int): PR 번호.
        title (str): PR 제목.
        body (Optional[str]): PR 본문.
        state (str): PR 상태 (open, closed).
        author (Author): PR 작성자.
        base_branch (str): Base 브랜치 (병합 대상).
        head_branch (str): Head 브랜치 (변경사항).
        base_sha (str): Base 브랜치의 커밋 SHA.
        head_sha (str): Head 브랜치의 커밋 SHA.
        repo_owner (str): 리포지토리 소유자.
        repo_name (str): 리포지토리 이름.
        files (list[FileChange]): 변경된 파일 목록.
        commits (list[CommitInfo]): 커밋 목록.
        total_additions (int): 전체 추가된 라인 수.
        total_deletions (int): 전체 삭제된 라인 수.
        total_changes (int): 전체 변경 라인 수.
        changed_files_count (int): 변경된 파일 개수.
        commits_count (int): 커밋 개수.
        html_url (Optional[str]): PR 웹 URL.
        diff_url (Optional[str]): PR diff URL.
    """

    # PR 기본 정보
    pr_number: int = Field(..., description="PR 번호")
    title: str = Field(..., description="PR 제목")
    body: Optional[str] = Field(None, description="PR 본문")
    state: str = Field(..., description="PR 상태 (open, closed)")
    author: Author = Field(..., description="PR 작성자")

    # 브랜치 정보
    base_branch: str = Field(..., description="Base 브랜치 (병합 대상)")
    head_branch: str = Field(..., description="Head 브랜치 (변경사항)")
    base_sha: str = Field(..., description="Base 브랜치의 커밋 SHA")
    head_sha: str = Field(..., description="Head 브랜치의 커밋 SHA")

    # 리포지토리 정보
    repo_owner: str = Field(..., description="리포지토리 소유자")
    repo_name: str = Field(..., description="리포지토리 이름")

    # 변경사항
    files: list[FileChange] = Field(default_factory=list, description="변경된 파일 목록")
    commits: list[CommitInfo] = Field(default_factory=list, description="커밋 목록")

    # 통계
    total_additions: int = Field(0, description="전체 추가된 라인 수")
    total_deletions: int = Field(0, description="전체 삭제된 라인 수")
    total_changes: int = Field(0, description="전체 변경 라인 수")
    changed_files_count: int = Field(0, description="변경된 파일 개수")
    commits_count: int = Field(0, description="커밋 개수")

    # URL
    html_url: Optional[str] = Field(None, description="PR 웹 URL")
    diff_url: Optional[str] = Field(None, description="PR diff URL")

    @property
    def has_files(self) -> bool:
        """변경된 파일이 있는지 확인.

        Returns:
            bool: 변경된 파일이 하나 이상 있으면 True.
        """
        return len(self.files) > 0

    @property
    def has_commits(self) -> bool:
        """커밋이 있는지 확인.

        Returns:
            bool: 커밋이 하나 이상 있으면 True.
        """
        return len(self.commits) > 0

    def get_file_by_name(self, filename: str) -> Optional[FileChange]:
        """파일명으로 FileChange 객체 찾기.

        Args:
            filename (str): 검색할 파일 경로.

        Returns:
            Optional[FileChange]: 일치하는 FileChange 객체, 없으면 None.
        """
        for file in self.files:
            if file.filename == filename:
                return file
        return None

    def get_files_by_extension(self, extension: str) -> list[FileChange]:
        """확장자로 파일 필터링.

        Args:
            extension (str): 필터링할 확장자 (예: '.py', '.ts').

        Returns:
            list[FileChange]: 해당 확장자를 가진 파일 목록.
        """
        return [f for f in self.files if f.filename.endswith(extension)]

    def get_modified_files_only(self) -> list[FileChange]:
        """수정된 파일만 반환 (추가/삭제 제외).

        Returns:
            list[FileChange]: 상태가 'modified'인 파일 목록.
        """
        return [f for f in self.files if f.status == "modified"]

    class Config:
        """Pydantic 설정."""

        json_schema_extra = {
            "example": {
                "pr_number": 123,
                "title": "Add new feature",
                "body": "This PR adds...",
                "state": "open",
                "author": {"login": "user123", "id": 1},
                "base_branch": "main",
                "head_branch": "feature/new-feature",
                "repo_owner": "company",
                "repo_name": "project",
                "files": [
                    {
                        "filename": "src/app.py",
                        "status": "modified",
                        "additions": 10,
                        "deletions": 5,
                        "changes": 15,
                        "patch": "@@ -1,5 +1,10 @@..."
                    }
                ],
                "total_additions": 10,
                "total_deletions": 5,
                "changed_files_count": 1
            }
        }
