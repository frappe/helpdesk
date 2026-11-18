"""Collect the four k6 runs into one table: perf/evidence/results.md"""

import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
rows = []
for path in sorted(out.glob("vus*_run*.json")):
    if path.name.endswith(".raw.json"):
        continue
    rows.append(json.loads(path.read_text())["result"])
rows.sort(key=lambda r: (r["vus"], r["run"]))

lines = [
    "| Users | Run | Requests (60 s) | Requests/s | Median ms | p95 ms | p95 limit ms | Unexpected failures | Failure limit | Within limits |",
    "|---|---|---|---|---|---|---|---|---|---|",
]
for r in rows:
    lines.append(
        f"| {r['vus']} | {r['run']} | {r['requests']} | {r['requests_per_second']:.1f} | {r['median_ms']:.1f} | "
        f"{r['p95_ms']:.1f} | {r['limits']['p95_ms']} | {r['unexpected_failure_rate'] * 100:.2f} % | < 1 % | "
        f"{'yes' if r['thresholds_passed'] else 'no'} |"
    )
(out / "results.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
