"""Build the final project report PDF from the team's Markdown documents.

    ~/report-venv/bin/python tests/team/tools/build_report.py OUT.pdf

Inputs (all in tests/team/):
  report/meta.yaml   title page: course, members, section, repository
  report/REPORT.md   the main report
  the documents listed in APPENDICES, reproduced in full as appendices

Diagrams written in Mermaid are drawn here: fishbones (RCA) with matplotlib,
other flowcharts (the control-flow graph) with Graphviz `dot`. SVG images
(the Pareto chart) are embedded with svglib.

Needs: reportlab, svglib, matplotlib, markdown-it-py, pyyaml; Graphviz.
"""

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph,
    Preformatted, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.fonts import addMapping

TEAM = Path(__file__).resolve().parents[1]

APPENDICES = [
    ("A", "Set-up, commands and repository layout", ["README.md"]),
    ("B", "Test plan", ["management/TEST_PLAN.md"]),
    ("C", "Estimation", ["management/ESTIMATION.md"]),
    ("D", "Risk register", ["management/RISK_REGISTER.md"]),
    ("E", "Traceability matrix", ["management/TRACEABILITY.md"]),
    ("F", "Root cause analysis", ["management/RCA.md"]),
    ("G", "Weekly progress report", ["management/PROGRESS_WEEK1.md"]),
    ("H", "Test completion report", ["management/TEST_COMPLETION_REPORT.md"]),
    ("I", "Defect log, Pareto and GQM", ["management/generated/DEFECT_SUMMARY.md"]),
    ("J", "API endpoint weaknesses", ["api/WEAKNESSES.md"]),
    ("K", "Static analysis and cyclomatic complexity", ["sonar/SONAR_REPORT.md", "sonar/CYCLOMATIC_COMPLEXITY.md"]),
    ("L", "Unit tests (MCC, MC/DC) and mutation analysis", ["unit/README.md", "mutation/SURVIVORS.md"]),
    ("M", "Use cases", ["e2e/USE_CASES.md"]),
    ("N", "Usability and accessibility", ["a11y/A11Y_REPORT.md"]),
    ("O", "Defensive security", ["security/SECURITY_REPORT.md"]),
    ("P", "Performance and recovery", ["perf/PERFORMANCE_REPORT.md"]),
    ("Q", "AI-use record", ["ai/AI_USE_RECORD.md"]),
    ("R", "Prompts", ["ai/PROMPTS.md"]),
]

# --- fonts and styles ----------------------------------------------------------

FONTS = {
    "Body": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "Body-Bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "Body-Italic": "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
    "Body-BoldItalic": "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
    "Mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "Mono-Bold": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
}
for name, path in FONTS.items():
    pdfmetrics.registerFont(TTFont(name, path))
addMapping("Body", 0, 0, "Body")
addMapping("Body", 1, 0, "Body-Bold")
addMapping("Body", 0, 1, "Body-Italic")
addMapping("Body", 1, 1, "Body-BoldItalic")
addMapping("Mono", 0, 0, "Mono")
addMapping("Mono", 1, 0, "Mono-Bold")
addMapping("Mono", 0, 1, "Mono")
addMapping("Mono", 1, 1, "Mono-Bold")

INK = colors.HexColor("#1F2933")
ACCENT = colors.HexColor("#1F4E79")
LINK = "#1A5FB4"
RULE = colors.HexColor("#B8C4CE")
HEAD_BG = colors.HexColor("#E6EDF3")

BODY = ParagraphStyle("body", fontName="Body", fontSize=9.2, leading=12.6, textColor=INK, spaceAfter=5)
QUOTE = ParagraphStyle("quote", parent=BODY, leftIndent=10, textColor=colors.HexColor("#3E4C59"),
                       borderPadding=(4, 6, 4, 6), backColor=colors.HexColor("#F2F5F8"), spaceBefore=3, spaceAfter=7)
H = {
    1: ParagraphStyle("h1", fontName="Body-Bold", fontSize=16, leading=20, textColor=ACCENT, spaceBefore=14, spaceAfter=8,
                      keepWithNext=1),
    2: ParagraphStyle("h2", fontName="Body-Bold", fontSize=12.5, leading=16, textColor=ACCENT, spaceBefore=11, spaceAfter=5,
                      keepWithNext=1),
    3: ParagraphStyle("h3", fontName="Body-Bold", fontSize=10.5, leading=14, textColor=INK, spaceBefore=8, spaceAfter=4,
                      keepWithNext=1),
    4: ParagraphStyle("h4", fontName="Body-Bold", fontSize=9.5, leading=13, textColor=INK, spaceBefore=6, spaceAfter=3,
                      keepWithNext=1),
}
CODE = ParagraphStyle("code", fontName="Mono", fontSize=7.2, leading=9, textColor=INK, backColor=colors.HexColor("#F4F6F8"),
                      borderPadding=4, leftIndent=4, rightIndent=4, spaceBefore=3, spaceAfter=8)
CAPTION = ParagraphStyle("caption", parent=BODY, fontSize=8, textColor=colors.HexColor("#52606D"), alignment=TA_CENTER)


def cell_style(size):
    return ParagraphStyle(f"cell{size}", fontName="Body", fontSize=size, leading=size * 1.28, textColor=INK)


# --- inline Markdown -> ReportLab markup ---------------------------------------

URL = re.compile(r"https?://[^\s<>|)\]]+[^\s<>|)\].,;:]")
ALLOWED_HTML = {"<br>": "<br/>", "<br/>": "<br/>", "<br />": "<br/>",
                "<super>": "<super>", "</super>": "</super>", "<sub>": "<sub>", "</sub>": "</sub>"}


def esc(text):
    return html.escape(text, quote=False)


def autolink(text):
    out, last = [], 0
    for m in URL.finditer(text):
        out.append(esc(text[last:m.start()]))
        url = m.group(0)
        out.append(f'<link href="{html.escape(url)}" color="{LINK}">{esc(url)}</link>')
        last = m.end()
    out.append(esc(text[last:]))
    return "".join(out)


def inline(children, code_size=None):
    parts, in_link = [], False
    for t in children or []:
        if t.type == "text":
            parts.append(esc(t.content) if in_link else autolink(t.content))
        elif t.type in ("strong_open", "strong_close"):
            parts.append("<b>" if t.type.endswith("open") else "</b>")
        elif t.type in ("em_open", "em_close"):
            parts.append("<i>" if t.type.endswith("open") else "</i>")
        elif t.type in ("s_open", "s_close"):
            parts.append("<strike>" if t.type.endswith("open") else "</strike>")
        elif t.type == "code_inline":
            size = f' size="{code_size}"' if code_size else ""
            parts.append(f'<font name="Mono"{size} color="#7A2E0E">{esc(t.content)}</font>')
        elif t.type == "link_open":
            href = t.attrGet("href") or ""
            if href.startswith("http"):
                parts.append(f'<link href="{html.escape(href)}" color="{LINK}">')
                in_link = True
        elif t.type == "link_close":
            if in_link:
                parts.append("</link>")
            in_link = False
        elif t.type == "softbreak":
            parts.append(" ")
        elif t.type == "hardbreak":
            parts.append("<br/>")
        elif t.type == "html_inline":
            parts.append(ALLOWED_HTML.get(t.content.strip().lower(), ""))
        elif t.type == "image":
            parts.append(esc(t.content))
    return "".join(parts).strip()


def plain(children):
    return re.sub(r"<[^>]+>", "", inline(children))


# --- diagrams --------------------------------------------------------------------

def fishbone_png(source, out):
    """Draw a Mermaid 'X["Cat<br/>• a<br/>• b"] --> E' cause list as a fishbone."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    causes, effect = [], ""
    for line in source.splitlines():
        m = re.match(r'\s*(\w+)\["(.+?)"\]\s*-->\s*\w+', line)
        if m:
            parts = [p.strip() for p in m.group(2).split("<br/>")]
            causes.append((parts[0], [p.lstrip("• ").strip() for p in parts[1:]]))
        m = re.match(r'\s*\w+\(\["(.+?)"\]\)', line)
        if m:
            effect = m.group(1).replace("<br/>", "\n")
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6.2)
    ax.axis("off")
    spine_y, spine_end = 3.1, 8.6
    ax.annotate("", xy=(spine_end, spine_y), xytext=(0.2, spine_y),
                arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#1F4E79"))
    ax.text(spine_end + 0.12, spine_y, effect, va="center", ha="left", fontsize=10, weight="bold",
            bbox=dict(boxstyle="round,pad=0.45", fc="#FCE8E6", ec="#B3261E"), wrap=True)
    top = causes[0::2]
    bottom = causes[1::2]
    import textwrap
    for row, items in ((1, top), (-1, bottom)):
        n = len(items)
        for i, (title, points) in enumerate(items):
            x_spine = 1.4 + i * (spine_end - 1.6) / max(n, 1) + 1.6
            x_end, y_end = x_spine - 1.25, spine_y + row * 2.15
            ax.plot([x_end, x_spine], [y_end, spine_y], color="#1F4E79", lw=1.4)
            ax.text(x_end, y_end + row * 0.18, title, ha="center", va="bottom" if row > 0 else "top",
                    fontsize=9.5, weight="bold", color="#1F4E79",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#E6EDF3", ec="#1F4E79"))
            for k, point in enumerate(points):
                frac = (k + 1) / (len(points) + 1)
                px = x_end + (x_spine - x_end) * frac
                py = y_end + (spine_y - y_end) * frac
                ax.text(px + 0.16, py, "\n".join(textwrap.wrap(point, 30)), fontsize=6.6,
                        va="center", ha="left", color="#1F2933")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)


def flowchart_png(source, out):
    """Translate a Mermaid flowchart (nodes, edges, edge labels) to Graphviz and render it."""
    lines = source.splitlines()
    direction = "TB" if re.search(r"flowchart\s+(TD|TB)", source) else "LR"
    shapes = {}
    edges = []
    # quoted labels first, so a label such as "N4: []" is read whole
    patterns = [
        (re.compile(r'(\w+)\s*\{"(.+)"\}$'), "diamond"),
        (re.compile(r'(\w+)\s*\{(.+)\}$'), "diamond"),
        (re.compile(r'(\w+)\s*\(\("?(.+?)"?\)\)$'), "circle"),
        (re.compile(r'(\w+)\s*\(\["(.+)"\]\)$'), "box"),
        (re.compile(r'(\w+)\s*\["(.+)"\]$'), "box"),
        (re.compile(r'(\w+)\s*\[(.+)\]$'), "box"),
    ]

    def note(token):
        token = token.strip()
        for pattern, shape in patterns:
            m = pattern.match(token)
            if m:
                label = m.group(2).replace("<br/>", "\\n").replace('"', '\\"')
                shapes.setdefault(m.group(1), (shape, label))
                return m.group(1)
        return token

    for line in lines[1:]:
        if "-->" not in line:
            if line.strip():
                note(line)
            continue
        left, right = line.split("-->", 1)
        label = ""
        m = re.match(r'\s*\|"?(.*?)"?\|\s*(.*)', right)
        if m:
            label, right = m.group(1), m.group(2)
        edges.append((note(left), note(right), label))
    dot = [f"digraph G {{ rankdir={direction}; node [fontname=\"DejaVu Sans\", fontsize=10, style=filled, "
           "fillcolor=\"#E6EDF3\", color=\"#1F4E79\"]; edge [fontname=\"DejaVu Sans\", fontsize=9, color=\"#52606D\"];"]
    for name, (shape, label) in shapes.items():
        extra = ", width=0.6, fixedsize=true, fillcolor=\"#FCE8E6\"" if shape == "circle" else ""
        dot.append(f'"{name}" [shape={shape}, label="{label}"{extra}];')
    for a, b, label in edges:
        dot.append(f'"{a}" -> "{b}" [label="{label}"];')
    dot.append("}")
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", "-o", str(out)], input="\n".join(dot), text=True, check=True)


def image_flowable(path, max_w, max_h=19 * cm):
    if path.suffix.lower() == ".svg":
        from svglib.svglib import svg2rlg
        drawing = svg2rlg(str(path))
        scale = min(max_w / drawing.width, max_h / drawing.height, 1.0)
        drawing.width, drawing.height = drawing.width * scale, drawing.height * scale
        drawing.scale(scale, scale)
        return drawing
    img = Image(str(path))
    scale = min(max_w / img.imageWidth, max_h / img.imageHeight)
    img.drawWidth, img.drawHeight = img.imageWidth * scale, img.imageHeight * scale
    return img


# --- block Markdown -> flowables ------------------------------------------------

class Heading(Paragraph):
    def __init__(self, text, style, toc_level=None, key=None):
        super().__init__(text, style)
        self.toc_level, self.key, self.plain = toc_level, key, re.sub(r"<[^>]+>", "", text)


class Renderer:
    def __init__(self, width, tmp):
        self.md = MarkdownIt("commonmark").enable("table").enable("strikethrough")
        self.width, self.tmp, self.n_img, self.n_key = width, tmp, 0, 0

    def key(self):
        self.n_key += 1
        return f"h{self.n_key}"

    def render(self, text, base_dir, shift=0, skip_first_h1=False, toc_max=2):
        tokens = self.md.parse(text)
        out, i, lists, quote = [], 0, [], 0
        skipped = not skip_first_h1
        while i < len(tokens):
            t = tokens[i]
            if t.type == "heading_open":
                level = int(t.tag[1])
                content = tokens[i + 1]
                if not skipped and level == 1:
                    skipped = True
                    i += 3
                    continue
                lvl = min(level + shift, 4)
                toc = lvl - 1 if lvl <= toc_max else None
                out.append(Heading(inline(content.children), H[lvl], toc, self.key()))
                i += 3
                continue
            if t.type in ("bullet_list_open", "ordered_list_open"):
                lists.append([t.type, int(t.attrGet("start") or 1)])
            elif t.type in ("bullet_list_close", "ordered_list_close"):
                lists.pop()
                if not lists:
                    out.append(Spacer(1, 3))
            elif t.type == "blockquote_open":
                quote += 1
            elif t.type == "blockquote_close":
                quote -= 1
            elif t.type == "paragraph_open":
                content = tokens[i + 1]
                kids = content.children or []
                images = [k for k in kids if k.type == "image"]
                if images and all(k.type == "image" or (k.type == "text" and not k.content.strip()) for k in kids):
                    for k in images:
                        path = (base_dir / k.attrGet("src")).resolve()
                        out.append(KeepTogether([image_flowable(path, self.width),
                                                 Paragraph(esc(k.content), CAPTION)]))
                    i += 3
                    continue
                markup = inline(kids)
                if lists and tokens[i - 1].type == "list_item_open":
                    kind = lists[-1]
                    bullet = "•" if kind[0] == "bullet_list_open" else f"{kind[1]}."
                    if kind[0] == "ordered_list_open":
                        kind[1] += 1
                    depth = len(lists)
                    style = ParagraphStyle(f"li{depth}", parent=BODY, leftIndent=12 * depth + 4,
                                           bulletIndent=12 * depth - 8, spaceAfter=2)
                    out.append(Paragraph(markup, style, bulletText=bullet))
                elif lists:
                    depth = len(lists)
                    out.append(Paragraph(markup, ParagraphStyle(f"lic{depth}", parent=BODY,
                                                                leftIndent=12 * depth + 4, spaceAfter=2)))
                else:
                    out.append(Paragraph(markup, QUOTE if quote else BODY))
                i += 3
                continue
            elif t.type == "table_open":
                j, rows, row = i + 1, [], None
                while tokens[j].type != "table_close":
                    tk = tokens[j]
                    if tk.type == "tr_open":
                        row = []
                    elif tk.type == "tr_close":
                        rows.append(row)
                    elif tk.type == "inline":
                        row.append(tk.children)
                    j += 1
                out.append(self.table(rows))
                out.append(Spacer(1, 6))
                i = j + 1
                continue
            elif t.type in ("fence", "code_block"):
                info = (t.info or "").strip()
                if info == "mermaid":
                    self.n_img += 1
                    png = self.tmp / f"diagram{self.n_img}.png"
                    if "flowchart LR" in t.content and "-->" in t.content and "E((" not in t.content and '(["' in t.content:
                        fishbone_png(t.content, png)
                    else:
                        flowchart_png(t.content, png)
                    out.append(image_flowable(png, self.width, 17 * cm))
                    out.append(Spacer(1, 6))
                else:
                    out.append(Preformatted(t.content.rstrip("\n"), CODE, maxLineLength=108, newLineChars=""))
            elif t.type == "hr":
                out.append(Spacer(1, 6))
            i += 1
        return out

    def table(self, rows):
        ncol = max(len(r) for r in rows)
        size = 8.2 if ncol <= 4 else 7.4 if ncol <= 6 else 6.6 if ncol <= 8 else 6.0
        style = cell_style(size)
        head = ParagraphStyle("head", parent=style, fontName="Body-Bold")
        lengths, longest_word = [0] * ncol, [0] * ncol
        for r_i, r in enumerate(rows):
            for c, cell in enumerate(r):
                text = html.unescape(plain(cell))
                lengths[c] = max(lengths[c], min(len(text), 70))
                font = "Body-Bold" if r_i == 0 else "Body"
                words = [pdfmetrics.stringWidth(w, font, size) for w in text.split()] or [0]
                longest_word[c] = max(longest_word[c], max(words))
        weights = [max(l, 4) ** 0.85 for l in lengths]
        total = sum(weights)
        widths = [self.width * w / total for w in weights]
        # never narrower than the longest word (capped, so a long path may still wrap)
        minimum = [min(max(w + 9, 1.1 * cm), 3.4 * cm) for w in longest_word]
        widths = [max(w, m) for w, m in zip(widths, minimum)]
        excess = sum(widths) - self.width
        if excess > 0:
            room = [w - m for w, m in zip(widths, minimum)]
            spare = sum(room)
            if spare > 0:
                widths = [w - excess * r / spare for w, r in zip(widths, room)]
        scale = self.width / sum(widths)
        widths = [w * scale for w in widths]
        data = []
        for r_i, r in enumerate(rows):
            cells = [Paragraph(inline(cell, code_size=size - 0.4), head if r_i == 0 else style) for cell in r]
            cells += [""] * (ncol - len(cells))
            data.append(cells)
        table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
            ("GRID", (0, 0), (-1, -1), 0.35, RULE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
        ]))
        return table


# --- document ------------------------------------------------------------------------

class Doc(BaseDocTemplate):
    def __init__(self, path, title, **kw):
        super().__init__(path, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                         bottomMargin=1.8 * cm, title=title, author="SE3002 group", **kw)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate("title", [frame], onPage=lambda c, d: None),
                               PageTemplate("body", [frame], onPage=self.decorate)])
        self.short_title = title

    def decorate(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Body", 7.5)
        canvas.setFillColor(colors.HexColor("#52606D"))
        canvas.drawString(self.leftMargin, A4[1] - 1.25 * cm, self.short_title)
        canvas.drawRightString(A4[0] - self.rightMargin, 1.05 * cm, f"Page {doc.page}")
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(self.leftMargin, A4[1] - 1.4 * cm, A4[0] - self.rightMargin, A4[1] - 1.4 * cm)
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Heading) and flowable.toc_level is not None:
            self.canv.bookmarkPage(flowable.key)
            self.canv.addOutlineEntry(flowable.plain, flowable.key, level=flowable.toc_level, closed=True)
            self.notify("TOCEntry", (flowable.toc_level, flowable.plain, self.page, flowable.key))


def title_page(meta):
    big = ParagraphStyle("t", fontName="Body-Bold", fontSize=22, leading=28, textColor=ACCENT, alignment=TA_CENTER)
    mid = ParagraphStyle("m", fontName="Body", fontSize=12.5, leading=17, textColor=INK, alignment=TA_CENTER)
    small = ParagraphStyle("s", parent=BODY, alignment=TA_CENTER)
    story = [Spacer(1, 3.2 * cm), Paragraph(esc(meta["course"]), mid), Spacer(1, 0.6 * cm),
             Paragraph(esc(meta["title"]), big), Spacer(1, 0.3 * cm), Paragraph(esc(meta["subtitle"]), mid),
             Spacer(1, 1.6 * cm)]
    rows = [[Paragraph("<b>Area</b>", BODY), Paragraph("<b>Member</b>", BODY), Paragraph("<b>Roll number</b>", BODY)]]
    areas = {"M1": "M1 · static analysis, white-box, mutation, CI",
             "M2": "M2 · API testing and data generation",
             "M3": "M3 · use cases, usability, accessibility, security, performance"}
    for m in meta["members"]:
        rows.append([Paragraph(esc(areas.get(m["area"], m["area"])), BODY), Paragraph(esc(m["name"]), BODY),
                     Paragraph(esc(m["roll"]), BODY)])
    table = Table(rows, colWidths=[8 * cm, 4.5 * cm, 3.5 * cm], hAlign="CENTER")
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, RULE), ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [table, Spacer(1, 1.0 * cm),
              Paragraph(f"Section: {esc(meta['section'])}", small),
              Paragraph(f"Group repository: {autolink(meta['repository'])}", small),
              Paragraph(f"System under test: {autolink(meta['upstream'])}", small),
              Spacer(1, 0.4 * cm), Paragraph(esc(meta["date"]), small)]
    return story


def build(out_pdf):
    meta = yaml.safe_load((TEAM / "report" / "meta.yaml").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        doc = Doc(str(out_pdf), f"{meta['course']} · Frappe Helpdesk final report")
        r = Renderer(doc.width, tmp)
        toc = TableOfContents()
        toc.levelStyles = [
            ParagraphStyle("toc0", fontName="Body-Bold", fontSize=9.5, leading=13, leftIndent=0, firstLineIndent=0),
            ParagraphStyle("toc1", fontName="Body", fontSize=8.5, leading=11, leftIndent=14, firstLineIndent=0),
        ]
        from reportlab.platypus.doctemplate import NextPageTemplate
        story = title_page(meta)
        story += [NextPageTemplate("body"), PageBreak(), Paragraph("Contents", H[1]), toc, PageBreak()]
        story += r.render((TEAM / "report" / "REPORT.md").read_text(), TEAM / "report", shift=0, toc_max=2)
        story += [PageBreak(), Heading("Appendices", H[1], 0, r.key()),
                  Paragraph("The documents below are reproduced in full from the repository "
                            "(<font name=\"Mono\">tests/team/</font>), in the state of the branch "
                            "<font name=\"Mono\">team/sqe-tests</font> when this report was built. "
                            "Raw evidence (JSON, logs, HTML reports) stays in the repository.", BODY)]
        for letter, title, files in APPENDICES:
            story += [PageBreak(), Heading(f"Appendix {letter}. {esc(title)}", H[1], 1, r.key()),
                      Paragraph(f"Source: <font name=\"Mono\">{', '.join('tests/team/' + f for f in files)}</font>",
                                CAPTION)]
            for k, f in enumerate(files):
                path = TEAM / f
                text = path.read_text()
                if len(files) > 1:
                    story += r.render(text, path.parent, shift=1, skip_first_h1=False, toc_max=0)
                else:
                    story += r.render(text, path.parent, shift=0, skip_first_h1=True, toc_max=0)
        doc.multiBuild(story)
    print(f"written: {out_pdf}")


if __name__ == "__main__":
    build(Path(sys.argv[1] if len(sys.argv) > 1 else "report.pdf").resolve())
