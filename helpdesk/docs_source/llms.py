import re
from collections import defaultdict, deque
from urllib.parse import urljoin, urlsplit

from helpdesk.docs_source.fetch import DocsFetchError, fetch
from helpdesk.docs_source.indexed import IndexedSource
from helpdesk.docs_source.text import has_dot_segment, plain_title, to_plain

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
            return bool(self._read_index(f"{self.url}/llms.txt")[1])
        except DocsFetchError:
            return False

    def read_pages(self) -> tuple[str, list[dict]]:
        label, pages = self._read_index(f"{self.url}/llms.txt", nested=True)
        bodies = self._read_bodies(pages)
        for page in pages:
            page["body"] = bodies.get(page["route"]) or page.pop("summary")
        return label, pages

    def _read_index(self, url: str, nested: bool = False) -> tuple[str, list[dict]]:
        text = fetch(url, self.host).text
        title = re.search(r"^# (.+)$", text, re.M)
        label = plain_title(title[1]) if title else self.host
        pages, children = {}, []
        for name, link, summary in LINE.findall(text):
            link = urljoin(url, link)
            path = urlsplit(link).path
            if urlsplit(link).hostname != self.host or not self._is_in_scope(path):
                continue
            if path.endswith("/llms.txt"):
                children.append(link)
            elif path.endswith(".md"):
                route = path.strip("/").removesuffix(".md")
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
        if nested:
            children = list(dict.fromkeys(children))
            self.truncated = len(children) > MAX_PARTS
            for child in children[:MAX_PARTS]:
                for page in self._read_index(child)[1]:
                    pages.setdefault(page["route"], page)
        return label, list(pages.values())

    def _read_bodies(self, pages: list[dict]) -> dict[str, str]:
        """Split llms-full.txt at each page title, in the order the titles appear."""
        waiting = defaultdict(deque)
        for page in pages:
            waiting[page["title"]].append(page["route"])
        bodies: dict[str, list[str]] = {}
        current = None
        for line in self._read_full().splitlines():
            title = plain_title(line[2:]) if line.startswith("# ") else None
            if title and waiting[title]:
                current = waiting[title].popleft()
                bodies[current] = []
            elif current:
                bodies[current].append(line)
        return {route: to_plain("\n".join(body)).strip() for route, body in bodies.items()}

    def _read_full(self) -> str:
        parts, url = [], f"{self.url}/llms-full.txt"
        try:
            while url and len(parts) < MAX_PARTS:
                text = fetch(url, self.host).text
                parts.append(text)
                following = NEXT_PART.search(text)
                url = urljoin(url, following[1]) if following else None
        except DocsFetchError:
            pass  # ponytail: titles and summaries still index
        return "\n".join(parts)

    def _is_in_scope(self, path: str) -> bool:
        base = self.base_path.rstrip("/")
        return path == base or path.startswith(f"{base}/")
