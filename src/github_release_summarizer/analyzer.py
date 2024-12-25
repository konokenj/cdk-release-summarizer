from pydantic.dataclasses import dataclass
import re
from typing import List, Tuple
from bs4 import BeautifulSoup, NavigableString, Tag
import requests


@dataclass
class PullRequest:
    category: str
    title: str
    pr_number: str


class PageAnalyzer:
    def get_pull_requests_from_release(self, url: str) -> List[PullRequest]:
        content = requests.get(url).text
        soup = BeautifulSoup(content, "html.parser")

        pull_requests = []

        # Features
        features_sections = soup.find_all("h3", string=re.compile("Features"))
        for features_section in features_sections:
            # Check if this section is under alpha modules
            is_alpha = (
                features_section.find_previous("h2", string=re.compile("Alpha modules"))
                is not None
            )
            prs = self._get_pull_requests_in_section(features_section)
            for pr in prs:
                if re.match(r"^update L1 CloudFormation resource definitions", pr[0]):
                    pull_requests.append(
                        PullRequest(category="L1", title=pr[0], pr_number=pr[1])
                    )
                else:
                    category = "alpha feature" if is_alpha else "feature"
                    pull_requests.append(
                        PullRequest(category=category, title=pr[0], pr_number=pr[1])
                    )

        # Bug Fixes
        bf_sections = soup.find_all("h3", string=re.compile("Bug Fixes"))
        for bf_section in bf_sections:
            # Check if this section is under alpha modules
            is_alpha = (
                bf_section.find_previous("h2", string=re.compile("Alpha modules"))
                is not None
            )
            prs = self._get_pull_requests_in_section(bf_section)
            for pr in prs:
                category = "alpha bug fix" if is_alpha else "bug fix"
                pull_requests.append(
                    PullRequest(category=category, title=pr[0], pr_number=pr[1])
                )

        # Sort pull requests by category order
        category_order = {
            "feature": 1,
            "L1": 2,
            "bug fix": 3,
            "alpha feature": 4,
            "alpha bug fix": 5,
        }
        pull_requests.sort(key=lambda x: category_order[x.category])

        return pull_requests

    def _get_pull_requests_in_section(
        self, section: Tag | NavigableString
    ) -> List[Tuple[str, str]]:
        results = []
        ul = section.find_next("ul")
        if isinstance(ul, Tag):
            for item in ul.find_all("li"):
                pr_text = item.text.strip()
                pr_title_match = re.search(r"(.*?) \(#\d+\)", pr_text)
                pr_number_match = re.search(r"#(\d+)", pr_text)

                if pr_title_match and pr_number_match:
                    title = pr_title_match.group(1)
                    pr_number = pr_number_match.group(1)
                    results.append((title, pr_number))

        return results

    def get_l1_update(self, content: str) -> List[str]:
        new_resources = []
        for resource in re.findall(r"\[\+\]\s+resource\s+(\S+)", content):
            new_resources.append(resource)

        for service in re.findall(r"\[\+\]\s+service\s+(\S+)", content):
            new_resources.append(service)

        return new_resources

    def get_related_issues(self, content: str) -> List[str]:
        issues = []
        for issue in re.findall(
            r"(close[sd]?|fixe?[sd]?|resolve[sd]?) #(\d+)", content, flags=re.IGNORECASE
        ):
            issues.append(issue[1])

        return issues

    def filter_comments_by_user(self, comments_data: List[dict]) -> List[str]:
        comments = []
        for comment in comments_data:
            if comment["user"]["type"] == "User":
                comments.append(comment["body"])
        return comments

    def filter_diff(self, diff_content: str, exclude_pattern: str = r"\.snapshot"):
        # Find all positions of "diff --git" at the start of lines
        positions = [
            m.start() for m in re.finditer(r"^diff --git", diff_content, re.MULTILINE)
        ]

        if len(positions) == 0:
            return diff_content

        filtered_chunks = []
        for i in range(len(positions)):
            start = positions[i]
            end = positions[i + 1] if i < len(positions) - 1 else len(diff_content)
            chunk = diff_content[start:end]

            if not chunk.strip():
                continue

            first_line = chunk.split("\n")[0]
            if not re.search(exclude_pattern, first_line):
                filtered_chunks.append(chunk)

        return "".join(filtered_chunks)
