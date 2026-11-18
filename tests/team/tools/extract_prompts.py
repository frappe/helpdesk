"""Write tests/team/ai/PROMPTS.md: every prompt the team typed, verbatim, from the session transcript."""
import json
import re
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
rows, asks = [], {}
for line in src.read_text(encoding="utf-8").splitlines():
    try:
        e = json.loads(line)
    except ValueError:
        continue
    msg, ts = e.get("message") or {}, e.get("timestamp", "")
    content = msg.get("content")
    if e.get("type") == "assistant":
        for c in content or []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "AskUserQuestion":
                asks[c["id"]] = c["input"].get("questions", [])
        continue
    if e.get("type") != "user" or e.get("isMeta") or e.get("isCompactSummary"):
        continue
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    for c in content or []:
        if not isinstance(c, dict):
            continue
        if c.get("type") == "tool_result" and c.get("tool_use_id") in asks:
            body = c.get("content")
            if isinstance(body, list):
                body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
            picked = re.findall(r'"="(.*?)"', str(body))
            for q, a in zip(asks[c["tool_use_id"]], picked):
                rows.append((ts, "choice", f"{q['question']}\n\nChosen: {a}"))
        elif c.get("type") == "text":
            t = re.sub(r"<system-reminder>.*?</system-reminder>", "", c["text"], flags=re.S).strip()
            if not t or t.startswith(("This session is being continued", "[SYSTEM NOTIFICATION", "Tool loaded")) \
                    or "<task-notification>" in t:
                continue
            m = re.match(r"<local-command-stdout>(.*)</local-command-stdout>", t, re.S)
            if m:
                rows.append((ts, "setting", m.group(1).strip()))
                continue
            rows.append((ts, "prompt", t))

lines = [
    "# Prompts",
    "",
    "Every prompt typed to the AI agent in this project, verbatim and in order,",
    "taken from the Claude Code session transcript by `tools/extract_prompts.py`.",
    "Times are UTC. \"choice\" rows are answers picked from options the agent",
    "offered; \"setting\" rows are changes made in the app, not prompts.",
    "Short prompts such as \"Mutation testing\" were the label of a button the",
    "agent offered as the next step.",
    "",
    "The full transcript, which also holds the agent's replies and every command",
    "it ran, is kept by the team outside the repository (it contains local paths",
    "and account details) and can be shown on request.",
    "",
]
for i, (ts, kind, text) in enumerate(rows, 1):
    text = EMAIL.sub("[email removed]", text)
    lines += [f"## {i}. {ts[:16].replace('T', ' ')} ({kind})", "", "```text", text, "```", ""]
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(lines))
print(len(rows), "entries written to", out)
