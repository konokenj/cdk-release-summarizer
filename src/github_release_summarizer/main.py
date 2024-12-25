import argparse
from typing import List
from analyzer import PageAnalyzer
from github_client import GitHubClient
from bedrock_client import BedrockClient, PullRequestData
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze GitHub Release Notes")
    parser.add_argument("url", help="GitHub release page URL")
    return parser.parse_args()


def main():
    args = parse_args()

    # get owner, repo and tag from url
    # ex. https://github.com/aws/aws-cdk/releases/tag/v2.172.0
    owner = args.url.split("/")[3]
    repo = args.url.split("/")[4]
    tag = args.url.split("/")[6]

    page_analyzer = PageAnalyzer()
    github_client = GitHubClient(token=os.environ["GITHUB_TOKEN"])
    bedrock_client = BedrockClient()

    # get PR list
    pull_requests = page_analyzer.get_pull_requests_from_release(args.url)

    japanese_authors = {}
    l1_updates = []

    for pr in pull_requests:
        issue = github_client.get_issue(owner, repo, pr.pr_number)
        description = issue["body"]

        if pr.category == "L1":
            l1_updates += page_analyzer.get_l1_update(description)

        else:
            related_issue_numbers = page_analyzer.get_related_issues(description)
            related_issue_descriptions = []
            for related_issue_number in related_issue_numbers:
                related_issue = github_client.get_issue(
                    owner, repo, related_issue_number
                )
                related_issue_descriptions.append(
                    f"#{related_issue_number}: {related_issue["body"]}"
                )

            diff = github_client.get_diff(owner, repo, pr.pr_number)
            diff = page_analyzer.filter_diff(diff)

            pr_data = PullRequestData(
                owner=owner,
                repo=repo,
                title=pr.title,
                description=description,
                related_issue_descriptions=related_issue_descriptions,
                diff=diff,
            )
            # print(pr_data.model_dump_json())
            summary_result = bedrock_client.generate_summary(pr_data)
            if summary_result.stop_reason != "end_turn":
                print(f"Unexpected stop reason: {summary_result.stop_reason}")

            summary = summary_result.text

            issue = github_client.get_issue(owner, repo, pr.pr_number)
            author = issue["user"]["login"]
            user = github_client.get_user(author)
            author_location = user["location"]
            author_twitter = user["twitter_username"]
            is_japanese_result = bedrock_client.generate_is_japanese(author_location)
            try:
                is_japanese = bedrock_client.validate_is_japanese(
                    is_japanese_result.text
                )
            except AssertionError:
                print(
                    f"Unexpected response: {is_japanese_result.text} for {author_location}"
                )
                is_japanese = False

            thank_you_message = ""
            if author_twitter and is_japanese:
                if pr.category == "feature":
                    thank_you_message = f"Thank you @{author_twitter}!"
                else:
                    if japanese_authors.get(author_twitter):
                        japanese_authors[author_twitter] += 1
                    else:
                        japanese_authors[author_twitter] = 1

            # pull request info
            print(
                f'\uf09b ({pr.category}) {pr.title} https://github.com/{owner}/{repo}/pull/{pr.pr_number} \ueb72 @{author} {"\uf188" if len(related_issue_numbers)>0 else ""} {",".join(related_issue_numbers)}'
            )
            # bedrock info
            print(
                f"\uf062 {summary_result.input_tokens} \uf063 {summary_result.output_tokens} ({summary_result.latency_ms}ms) \uf031 {len(summary)}"
            )
            print(f"{summary}{thank_you_message}")
            print()

    messages: List[str] = []
    for japanese_author in japanese_authors:
        if japanese_authors[japanese_author] > 1:
            messages.append(
                f"@{japanese_author} ({japanese_authors[japanese_author]}件)"
            )
        else:
            messages.append(f"@{japanese_author}")

    print(f"L1コンストラクト追加: \n{"\n".join(l1_updates)}\n")
    print()
    print(f"バグ修正およびalphaモジュールへの貢献: Thank you {", ".join(messages)}!!")
    print()


if __name__ == "__main__":
    main()
