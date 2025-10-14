from helpdesk.api.otto.types import SummaryConfig


default_summary_directive = """
Be to the point
""".strip()

default_summary_config = SummaryConfig(
    enabled=False,
    llm="",
    directive=default_summary_directive,
    include_comments=False,
)
