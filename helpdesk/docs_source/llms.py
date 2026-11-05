import re
from collections import defaultdict, deque
from urllib.parse import urljoin, urlsplit

from helpdesk.docs_source.fetch import DocsFetchError, fetch
from helpdesk.docs_source.indexed import IndexedSource
from helpdesk.docs_source.text import clean_markdown, has_dot_segment, plain_title, to_plain

MAX_PARTS = 20
LINE = re.compile(r"^\s*[-*] \[(.+?)\]\((\S+?)\)(?:: (.*))?$", re.M)
NEXT_PART = re.compile(r"^> Next part: (\S+)", re.M)


class LlmsSource(IndexedSource):
    """Any site with llms.txt: indexed here, pages read as Markdown."""

    def __init__(self, url: str) -> None:
        super().__init__(url)
        self.base_path = urlsplit(self.url).path

    def is_available(self) -> bool:
        try:
            _, pages, children = self._parse(f"{self.url}/llms.txt")
            return bool(pages or children)
        except DocsFetchError:
            return False

    def read_pages(self) -> tuple[str, list[dict]]:
        label, pages = self._read_index(f"{self.url}/llms.txt")
        bodies = self._read_bodies(pages)
        for page in pages:
            summary = page.pop("summary")
            page["body"] = bodies.get(page["route"]) or summary
        return label, pages

    def _read_index(self, url: str) -> tuple[str, list[dict]]:
        label, pages, children = self._parse(url)
        pages = {page["route"]: page for page in pages}
        if url == f"{self.url}/llms.txt":
            self.truncated = len(children) > MAX_PARTS
            for child in children[:MAX_PARTS]:
                for page in self._parse(child)[1]:
                    pages.setdefault(page["route"], page)
        return label, list(pages.values())

    def _parse(self, url: str) -> tuple[str, list[dict], list[str]]:
        """The label, the pages and the child index URLs of one llms.txt."""
        text = fetch(url, self.host).text
        title = re.search(r"^# (.+)$", text, re.M)
        label = plain_title(title[1]) if title else self.host
        pages, children = {}, []
        for name, link, summary in LINE.findall(text):
            try:
                link = urljoin(url, link)
                parts = urlsplit(link)
                host = parts.hostname
            except ValueError:
                continue
            if host != self.host or not self._is_in_scope(parts.path):
                continue
            if parts.path.endswith("/llms.txt"):
                children.append(link)
            elif parts.path.endswith(".md"):
                route = parts.path.strip("/").removesuffix(".md")
                if route and not has_dot_segment(route):
                    pages.setdefault(
                        route,
                        {
                            "route": route,
                            "title": plain_title(name),
                            "url": link,
                            "summary": summary,
                        },
                    )
        return label, list(pages.values()), list(dict.fromkeys(children))

    def _read_bodies(self, pages: list[dict]) -> dict[str, str]:
        """Split llms-full.txt at each page title; any other H1 ends the page."""
        waiting = defaultdict(deque)
        titles = {}
        for page in pages:
            waiting[page["title"]].append(page["route"])
            titles[page["route"]] = page["title"]
        bodies: dict[str, list[str]] = {}
        current, in_code = None, False
        for line in self._read_full().splitlines():
            if line.startswith("```"):
                in_code = not in_code
            title = plain_title(line[2:]) if line.startswith("# ") and not in_code else None
            if title is not None:
                current = waiting[title].popleft() if waiting[title] else None
                if current:
                    bodies[current] = []
            elif current:
                bodies[current].append(line)
        return {
            route: " ".join(to_plain(clean_markdown("\n".join(body), titles[route])).split())
            for route, body in bodies.items()
        }

    def _read_full(self) -> str:
        parts, url = [], f"{self.url}/llms-full.txt"
        try:
            while url and len(parts) < MAX_PARTS:
                text = fetch(url, self.host).text
                parts.append(text)
                following = NEXT_PART.search(text)
                url = urljoin(url, following[1]) if following else None
        except (DocsFetchError, ValueError):
            pass  # ponytail: titles and summaries still index
        return "\n".join(parts)

    def _is_in_scope(self, path: str) -> bool:
        base = self.base_path.rstrip("/")
        return path == base or path.startswith(f"{base}/")
