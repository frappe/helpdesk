from typing import TypedDict


class FeatureFlags(TypedDict):
    summary: bool


class SummaryConfig(TypedDict, total=False):
    enabled: bool
    llm: str
    guidelines: str
    reasoning_effort: str


class FeatureConfig(TypedDict):
    summary: SummaryConfig


class Summary(TypedDict):
    creation: str
    content: str
    summarizer: str # User Name
    summarized_by: str # User Email
    snippet: str
