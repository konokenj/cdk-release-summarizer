# GitHub Release Summarizer

> [!WARNING]
> これは個人利用のための実験的なリポジトリです

GitHub でホストされている OSS の Release Note を分析して、各 Pull Request の要約を Amazon Bedrock で作成します。

現在は aws/aws-cdk にのみ対応しています。

## How to use

AWS CLI の認証はあらかじめ済ませておいてください。GitHub API の呼び出しには Personal Access Token が必要です。

```sh
export GITHUB_TOKEN=xxxxxxxxxxxxxxxxxxxxx
poetry install
poetry run python src/github_release_summarizer/main.py https://github.com/aws/aws-cdk/releases/tag/v2.173.0
```

## Testing

```sh
poetry run python -m pytest tests/unit/
```
