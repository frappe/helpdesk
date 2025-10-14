from typing import TypedDict


class FeatureFlags(TypedDict, total=False):
    summary: bool


class SummaryConfig(TypedDict, total=False):
    enabled: bool
    llm: str
    directive: str
    include_comments: bool


class FeatureConfig(TypedDict, total=False):
    summary: SummaryConfig


class Summary(TypedDict):
    creation: str
    content: str
    summarizer: str
    summarized_by: str
    snippet: str
