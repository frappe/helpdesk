"""Summarise a ZAP passive run: alerts grouped by type, and the route inventory.

Usage: python3 zap_summary.py <evidence/zap dir>
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

RISK_ORDER = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}


def route_of(url):
    """Collapse ids and query strings so one endpoint is one route."""
    parsed = urlparse(url)
    path = re.sub(r"/\d+(?=/|$)", "/{id}", parsed.path)
    path = re.sub(r"/assets/.*", "/assets/...", path)
    return path


def main(out):
    out = Path(out)
    alerts = json.loads((out / "alerts.json").read_text())["alerts"]
    urls = json.loads((out / "urls.json").read_text())["urls"]
    messages = json.loads((out / "message_count.json").read_text())["numberOfMessages"]

    grouped = defaultdict(lambda: {"count": 0, "urls": set(), "evidence": set()})
    for alert in alerts:
        key = (alert["risk"], alert["alert"], alert["pluginId"], alert.get("cweid", ""), alert["confidence"])
        group = grouped[key]
        group["count"] += 1
        group["urls"].add(route_of(alert["url"]))
        if alert.get("param"):
            group["evidence"].add(f"param {alert['param']}")
        elif alert.get("evidence"):
            group["evidence"].add(alert["evidence"][:80])
        group["solution"] = alert.get("solution", "").strip().split("\n")[0][:160]

    lines = [
        "# ZAP passive scan summary",
        "",
        f"Messages proxied: {messages}. Distinct URLs seen: {len(urls)}. Alert instances: {len(alerts)}.",
        "",
        "| Risk | Alert | Plugin | CWE | Confidence | Instances | Routes (sample) | Evidence (sample) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for (risk, name, plugin, cwe, confidence), g in sorted(grouped.items(), key=lambda kv: (RISK_ORDER.get(kv[0][0], 9), kv[0][1])):
        routes = ", ".join(sorted(g["urls"])[:4]) + (f" (+{len(g['urls']) - 4})" if len(g["urls"]) > 4 else "")
        ev = "; ".join(sorted(g["evidence"])[:3])
        lines.append(f"| {risk} | {name} | {plugin} | {cwe} | {confidence} | {g['count']} | {routes} | {ev} |")

    routes = defaultdict(set)
    for url in urls:
        parsed = urlparse(url)
        if parsed.netloc and not parsed.path.startswith("/assets/"):
            routes[route_of(url)].add(url.split("?")[0])
    lines += ["", "## Routes observed (excluding static assets)", ""]
    lines += [f"- `{route}`" for route in sorted(routes)]
    (out / "zap_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:4 + len(grouped) + 2]))


if __name__ == "__main__":
    main(sys.argv[1])
