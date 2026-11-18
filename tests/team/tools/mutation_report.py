"""Summarise a Cosmic Ray session and gate on the mutation score.

Mutation score = killed / (killed + survived). Mutants skipped by the scope
filter and "incompetent" mutants (the mutated file could not even be run) are
reported but do not count either way.

Usage: python mutation_report.py <session.sqlite> [--out DIR] [--threshold PCT]
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import TestOutcome, WorkerOutcome


def classify(result):
    if result.worker_outcome == WorkerOutcome.SKIPPED:
        return "skipped"
    if result.worker_outcome != WorkerOutcome.NORMAL:
        return "abnormal"
    if result.test_outcome == TestOutcome.KILLED:
        return "killed"
    if result.test_outcome == TestOutcome.SURVIVED:
        return "survived"
    return "incompetent"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("session")
    parser.add_argument("--out", default=None)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    totals = Counter()
    by_operator = defaultdict(Counter)
    by_file = defaultdict(Counter)
    survivors = []
    with use_db(args.session, WorkDB.Mode.open) as db:
        pending = sum(1 for _ in db.pending_work_items)
        for item, result in db.completed_work_items:
            mutation = item.mutations[0]
            outcome = classify(result)
            totals[outcome] += 1
            if outcome == "skipped":
                continue
            file_name = Path(str(mutation.module_path)).name
            by_operator[mutation.operator_name][outcome] += 1
            by_file[file_name][outcome] += 1
            if outcome == "survived":
                survivors.append(
                    {
                        "job_id": item.job_id,
                        "file": file_name,
                        "line": mutation.start_pos[0],
                        "operator": mutation.operator_name,
                        "occurrence": mutation.occurrence,
                        "diff": result.diff or "",
                    }
                )

    killed, survived = totals["killed"], totals["survived"]
    judged = killed + survived
    score = 100.0 * killed / judged if judged else 0.0
    survivors.sort(key=lambda s: (s["file"], s["line"], s["operator"]))

    lines = [
        "# Mutation report",
        "",
        f"- Mutants in scope: {judged + totals['incompetent'] + totals['abnormal']}",
        f"- Killed: {killed}",
        f"- Survived: {survived}",
        f"- Incompetent (not runnable): {totals['incompetent']}",
        f"- Abnormal / timeout: {totals['abnormal']}",
        f"- Skipped (outside scope): {totals['skipped']}",
        f"- Still pending: {pending}",
        f"- **Mutation score: {score:.1f}%** (killed / (killed + survived))",
        "",
        "## By file",
        "",
        "| File | Killed | Survived | Score |",
        "|---|---|---|---|",
    ]
    for name, c in sorted(by_file.items()):
        j = c["killed"] + c["survived"]
        lines.append(f"| {name} | {c['killed']} | {c['survived']} | {100.0 * c['killed'] / j if j else 0:.1f}% |")
    lines += ["", "## By operator", "", "| Operator | Killed | Survived |", "|---|---|---|"]
    for name, c in sorted(by_operator.items()):
        lines.append(f"| {name} | {c['killed']} | {c['survived']} |")
    lines += ["", f"## Surviving mutants ({len(survivors)})", ""]
    for number, s in enumerate(survivors, 1):
        lines += [
            f"### S{number}. {s['file']}:{s['line']} — {s['operator']} (occurrence {s['occurrence']})",
            "",
            "```diff",
            s["diff"].strip(),
            "```",
            "",
        ]
    report = "\n".join(lines)

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "mutation_report.md").write_text(report)
        (out / "mutation_summary.json").write_text(
            json.dumps(
                {
                    "score": round(score, 2),
                    "totals": dict(totals),
                    "pending": pending,
                    "by_file": {k: dict(v) for k, v in by_file.items()},
                    "by_operator": {k: dict(v) for k, v in by_operator.items()},
                    "survivors": survivors,
                },
                indent=2,
            )
        )
    print(report if not args.out else "\n".join(lines[: lines.index("## By operator")]))

    if pending:
        print(f"FAIL: {pending} mutants were never executed")
        return 1
    if args.threshold is not None and score < args.threshold:
        print(f"FAIL: mutation score {score:.1f}% is below the {args.threshold:.1f}% gate")
        return 1
    if args.threshold is not None:
        print(f"PASS: mutation score {score:.1f}% meets the {args.threshold:.1f}% gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
