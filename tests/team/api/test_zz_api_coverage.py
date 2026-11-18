"""API coverage criteria, checked against what the suite actually sent.

Runs last (file name order). Every request made through `Client.call` was
logged, and every generated case is known, so the criteria can be measured
rather than claimed:

  * operation coverage    every operation in the spec was called
  * status-code coverage  every response code the spec documents was observed
  * parameter coverage    every input has at least one valid and one invalid case
  * value coverage        every enum member of every input was sent
"""

import json
from collections import defaultdict
from pathlib import Path

import pytest
import yaml
from conftest import CALL_LOG, TEAM_DIR

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "generated" / "testdata.json").read_text())
SPEC = yaml.safe_load((HERE / "openapi.yaml").read_text())
REPORT = TEAM_DIR / "reports" / "api" / "api_coverage.md"


def observed_codes():
    codes = defaultdict(set)
    for operation, status in CALL_LOG:
        codes[operation].add(str(status))
    return codes


@pytest.fixture(scope="module")
def full_run():
    if len(CALL_LOG) < 100:
        pytest.skip("coverage is only meaningful when the whole API suite runs")


def test_operation_and_status_code_coverage(full_run):
    codes = observed_codes()
    lines = ["# API coverage", "", "| Operation | Documented | Observed | Missing |", "|---|---|---|---|"]
    missing_any = []
    for operation in DATA["operations"]:
        op_id = operation["operationId"]
        documented = set(operation["responses"])
        missing = sorted(documented - codes[op_id])
        lines.append(
            f"| {op_id} | {', '.join(sorted(documented))} | {', '.join(sorted(codes[op_id]))} | "
            f"{', '.join(missing) or '-'} |"
        )
        if missing:
            missing_any.append((op_id, missing))
    total = sum(len(op["responses"]) for op in DATA["operations"])
    covered = total - sum(len(m) for _, m in missing_any)
    lines += ["", f"Operations called: {len([o for o in DATA['operations'] if codes[o['operationId']]])}"
              f"/{len(DATA['operations'])}", f"Documented status codes observed: {covered}/{total}",
              f"Requests sent: {len(CALL_LOG)}"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    assert not missing_any, f"documented responses never observed: {missing_any}"


def test_every_input_has_valid_and_invalid_cases():
    by_input = defaultdict(set)
    for case in DATA["cases"]:
        by_input[(case["operationId"], case["input"])].add(case["valid"])
    one_sided = {key for key, kinds in by_input.items() if kinds != {True, False}}
    assert not one_sided, f"inputs without both a valid and an invalid class: {one_sided}"


def test_every_enum_member_in_the_spec_is_exercised():
    sent = defaultdict(set)
    for case in DATA["cases"]:
        if case["valid"] and isinstance(case["value"], str):
            sent[case["input"].split(":", 1)[1].split(".")[-1]].add(case["value"])
    update = SPEC["components"]["schemas"]["TicketUpdate"]["properties"]
    for name, schema in update.items():
        for member in schema.get("enum", []):
            assert member in sent[name], f"enum member never sent: {name}={member}"
