"""Defect summary, Pareto analysis and GQM metrics from the defect log.

Reads  management/defects.yaml        (the defect log)
       management/TRACEABILITY.md      (requirement rows and their result)
       sonar/evidence/main/files.json  (lines of code per file, for density)
Writes management/generated/DEFECT_SUMMARY.md and pareto.svg

Usage: python tools/defects_report.py [--as-of YYYY-MM-DD]
"""

import argparse
import collections
import datetime
import json
import re
from pathlib import Path

import yaml

TEAM = Path(__file__).resolve().parents[1]
MGMT = TEAM / "management"
OUT = MGMT / "generated"

SEVERITY_ORDER = ["Critical", "Major", "Minor", "Trivial"]
OPEN_STATES = {"New", "Open", "Reopened"}
# defects that count as product defects (Rejected / Not a defect excluded)
COUNTED = lambda d: d["status"] != "Rejected"


def load_defects():
    return yaml.safe_load((MGMT / "defects.yaml").read_text())


def ncloc_by_file():
    files = json.loads((TEAM / "sonar/evidence/main/files.json").read_text())
    result = {}
    for f in files:
        for m in f.get("measures", []):
            if m["metric"] == "ncloc":
                result[f["path"]] = int(float(m["value"]))
    return result


def requirement_rows():
    rows = []
    for line in (MGMT / "TRACEABILITY.md").read_text().splitlines():
        if re.match(r"\| (FR|BR)-?[A-Z0-9]+ ", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append({"id": cells[0], "result": cells[-1]})
    return rows


def pareto_svg(rows, path):
    """Bars (count per category, descending) and cumulative-% line."""
    width, height, left, bottom, top = 760, 380, 60, 120, 30
    plot_w, plot_h = width - left - 60, height - bottom - top
    total = sum(c for _, c in rows)
    peak = max(c for _, c in rows)
    bar_w = plot_w / len(rows)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'font-family="Arial, sans-serif" font-size="11">',
             f'<rect width="{width}" height="{height}" fill="white"/>',
             f'<text x="{width/2}" y="18" text-anchor="middle" font-size="14" font-weight="bold">'
             f'Defects by category (Pareto), n = {total}</text>']
    # axes
    x0, y0 = left, top + plot_h
    parts.append(f'<line x1="{x0}" y1="{top}" x2="{x0}" y2="{y0}" stroke="#333"/>')
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0 + plot_w}" y2="{y0}" stroke="#333"/>')
    parts.append(f'<line x1="{x0 + plot_w}" y1="{top}" x2="{x0 + plot_w}" y2="{y0}" stroke="#333"/>')
    for i in range(0, peak + 1, max(1, peak // 5)):
        y = y0 - plot_h * i / peak
        parts.append(f'<text x="{x0 - 6}" y="{y + 4}" text-anchor="end">{i}</text>')
    for pct in (0, 20, 40, 60, 80, 100):
        y = y0 - plot_h * pct / 100
        parts.append(f'<text x="{x0 + plot_w + 6}" y="{y + 4}">{pct}%</text>')
    y80 = y0 - plot_h * 0.8
    parts.append(f'<line x1="{x0}" y1="{y80}" x2="{x0 + plot_w}" y2="{y80}" stroke="#999" stroke-dasharray="4 3"/>')
    parts.append(f'<text x="{x0 - 40}" y="{top - 8}">defects</text>')
    parts.append(f'<text x="{x0 + plot_w - 10}" y="{top - 8}">cumulative</text>')
    cumulative, points = 0, []
    for i, (category, count) in enumerate(rows):
        x = x0 + i * bar_w + bar_w * 0.15
        h = plot_h * count / peak
        parts.append(f'<rect x="{x:.1f}" y="{y0 - h:.1f}" width="{bar_w * 0.7:.1f}" height="{h:.1f}" fill="#4a78b5"/>')
        parts.append(f'<text x="{x + bar_w * 0.35:.1f}" y="{y0 - h - 4:.1f}" text-anchor="middle">{count}</text>')
        cx = x0 + (i + 0.5) * bar_w
        label = category.replace(" / ", "/").split(" (")[0]
        parts.append(f'<text transform="translate({cx:.1f},{y0 + 10}) rotate(35)" text-anchor="start">{label}</text>')
        cumulative += count
        points.append((cx, y0 - plot_h * cumulative / total))
    parts.append('<polyline fill="none" stroke="#d0582c" stroke-width="2" points="'
                 + " ".join(f"{x:.1f},{y:.1f}" for x, y in points) + '"/>')
    for x, y in points:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#d0582c"/>')
    parts.append("</svg>")
    path.write_text("\n".join(parts))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=datetime.date.today().isoformat())
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)

    defects = load_defects()
    counted = [d for d in defects if COUNTED(d)]
    out = [f"# Defect summary (generated {args.as_of} by tools/defects_report.py)", ""]

    # log table
    out += ["## Defect log", "",
            "| ID | Ref | Title | Category | Severity | Priority | Status | Triage | Risk | Issue |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for d in defects:
        issue = f"#{d['issue']}" if d.get("issue") else "to file"
        status = d["status"] + (f" ({d['note']})" if d.get("note") else "")
        out.append(f"| {d['id']} | {d['ref']} | {d['title']} | {d['category']} | {d['severity']} | "
                   f"{d['priority']} | {status} | {d['triage']} | {', '.join(d.get('risk', [])) or '-'} | {issue} |")
    out.append("")

    # severity x status
    sev = collections.Counter((d["severity"], d["status"] in OPEN_STATES) for d in counted)
    out += ["## By severity", "", "| Severity | Open | Fixed / closed | Total |", "|---|---|---|---|"]
    for s in SEVERITY_ORDER:
        o, c = sev[(s, True)], sev[(s, False)]
        if o + c:
            out.append(f"| {s} | {o} | {c} | {o + c} |")
    out.append(f"| **All** | {sum(v for (s, o), v in sev.items() if o)} | "
               f"{sum(v for (s, o), v in sev.items() if not o)} | {len(counted)} |")
    out += ["", f"Excluded: {len(defects) - len(counted)} rejected (not a defect).", ""]

    # Pareto
    by_cat = collections.Counter(d["category"] for d in counted)
    rows = by_cat.most_common()
    total = sum(c for _, c in rows)
    out += ["## Pareto by category", "", "![Pareto chart](pareto.svg)", "",
            "| Category | Defects | % | Cumulative % | Of which Major |", "|---|---|---|---|---|"]
    cumulative = 0
    for category, count in rows:
        cumulative += count
        major = sum(1 for d in counted if d["category"] == category and d["severity"] in ("Critical", "Major"))
        out.append(f"| {category} | {count} | {100 * count / total:.0f} | {100 * cumulative / total:.0f} | {major} |")
    out.append("")
    pareto_svg(rows, OUT / "pareto.svg")

    # GQM metrics
    ncloc = ncloc_by_file()
    python_kloc = sum(v for p, v in ncloc.items() if p.endswith(".py")) / 1000
    backend = [d for d in counted if d["layer"] == "backend"]
    in_ticket = [d for d in backend if str(d.get("file", "")).endswith("hd_ticket/hd_ticket.py")]
    ticket_kloc = ncloc["helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py"] / 1000
    fixed = [d for d in counted if d["status"] not in OPEN_STATES]
    reopened = sum(d.get("reopened", 0) for d in counted)
    reqs = requirement_rows()
    tested = [r for r in reqs if r["result"] != "Not tested"]
    passing = [r for r in reqs if r["result"].startswith("Pass")]
    out += ["## GQM metrics", "",
            "| Metric | Definition | Value |", "|---|---|---|",
            f"| Defect density, backend | backend defects / Python KLOC ({python_kloc:.1f}) | "
            f"{len(backend)} / {python_kloc:.1f} = **{len(backend) / python_kloc:.2f} per KLOC** |",
            f"| Defect density, `hd_ticket.py` | defects rooted in the file / its KLOC ({ticket_kloc:.2f}) | "
            f"{len(in_ticket)} / {ticket_kloc:.2f} = **{len(in_ticket) / ticket_kloc:.1f} per KLOC** |",
            f"| Requirements coverage (tested) | requirements with at least one executed test / all | "
            f"{len(tested)} / {len(reqs)} = **{100 * len(tested) / len(reqs):.0f} %** |",
            f"| Requirements coverage (passing) | requirements with no failing test and no open Major defect / all | "
            f"{len(passing)} / {len(reqs)} = **{100 * len(passing) / len(reqs):.0f} %** |",
            f"| Reopen rate | reopenings / defects fixed | "
            + (f"{reopened} / {len(fixed)} = **{100 * reopened / len(fixed):.0f} %** |" if fixed else "no fixes yet |"),
            ""]
    (OUT / "DEFECT_SUMMARY.md").write_text("\n".join(out))
    print("\n".join(out[-12:]))
    print(f"Pareto: {rows}")


if __name__ == "__main__":
    main()
