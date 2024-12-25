from functools import cache
import re
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
import boto3
from typing import List


class PullRequestData(BaseModel):
    owner: str
    repo: str
    title: str
    description: str
    related_issue_descriptions: List[str]
    diff: str


class ConverseResult(BaseModel):
    text: str
    stop_reason: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class BedrockClient:
    def __init__(self):
        self.client = boto3.client("bedrock-runtime")

    def generate_summary(self, pr_data: PullRequestData) -> ConverseResult:
        prompt = self._create_summary_prompt(pr_data)

        response = self.client.converse(
            modelId="us.amazon.nova-lite-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            inferenceConfig={
                "temperature": 0.0,
            },
        )

        return ConverseResult(
            text=response["output"]["message"]["content"][0]["text"],
            stop_reason=response["stopReason"],
            input_tokens=response["usage"]["inputTokens"],
            output_tokens=response["usage"]["outputTokens"],
            latency_ms=response["metrics"]["latencyMs"],
        )

    def _create_summary_prompt(self, pr: PullRequestData) -> str:
        return f"""\
あなたは開発者向けにOSSの新機能をTwitterで説明するDeveloper Advocateです。マージされたPull Requestのデータを元に、この変更の簡潔な要約を作成してください。

<title>{pr.title}</title>

<description>{pr.description}</description>

<resolvedIssues>
{"\n==========\n".join(pr.related_issue_descriptions)}
</resolvedIssues>

<diff>{pr.diff}</diff>

<outputRule>140文字以内の日本語で簡潔に要約してください。ソフトウェアのモジュール名や機能名、サービス名は英語のままにしてください。最初の一文で影響のあるモジュールと簡潔な要約を示し、必要であれば次の文でそれがどのような機能であるかの説明や、解決される問題を加えてください。back quoteや改行は出力しないでください。</outputRule>\
"""

    def generate_is_japanese(self, location: str) -> ConverseResult:
        prompt = self._create_is_japanese_prompt(location)

        response = self.client.converse(
            modelId="us.amazon.nova-micro-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            inferenceConfig={
                "temperature": 0.0,
            },
        )

        return ConverseResult(
            text=response["output"]["message"]["content"][0]["text"],
            stop_reason=response["stopReason"],
            input_tokens=response["usage"]["inputTokens"],
            output_tokens=response["usage"]["outputTokens"],
            latency_ms=response["metrics"]["latencyMs"],
        )

    def validate_is_japanese(self, text: str) -> bool:
        if not re.match(r"^[01]$", text):
            raise AssertionError(f"Unexpected response: {text}")

        return text == "1"

    def _create_is_japanese_prompt(self, location: str) -> str:
        return f"""\
これはGitHubアカウントのLocationにセットされた値です。このアカウントが日本に居住している人かどうかを判断してください。日本に居住している場合は1を、そうでない場合や確信が持てない場合は0を返してください。応答には0か1のみを含め、他の出力は含めないでください。
<location>{location}</location>\
"""
