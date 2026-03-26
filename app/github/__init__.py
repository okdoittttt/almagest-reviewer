from .client import GitHubClient
from .pr_collector import PRDataCollector

github_client = GitHubClient()
pr_collector = PRDataCollector(github_client)

__all__ = ["GitHubClient", "PRDataCollector", "github_client", "pr_collector"]