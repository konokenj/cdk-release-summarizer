import re
from typing import List
import requests

API_BASE_URL = "https://api.github.com/"


class GitHubClient:
    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }
        )

    def get_issue(self, owner: str, repo: str, pr_number: str) -> dict:
        url = f"{API_BASE_URL}/repos/{owner}/{repo}/issues/{pr_number}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_user(self, username: str) -> dict:
        url = f"{API_BASE_URL}/users/{username}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_issue_comments(self, owner: str, repo: str, pr_number: str) -> List[str]:
        url = f"{API_BASE_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_diff(self, owner: str, repo: str, pr_number: str) -> str:
        response = requests.get(
            f"https://patch-diff.githubusercontent.com/raw/{owner}/{repo}/pull/{pr_number}.diff",
            allow_redirects=False,
        )
        return response.text
