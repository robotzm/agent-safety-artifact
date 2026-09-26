#!/usr/bin/env python3
"""Check static website references using only the Python standard library.

Usage: python3 scripts/check_links.py [path/to/docs]
External URLs are checked for obvious placeholders, not fetched over the network.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE | re.DOTALL)
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
PLACEHOLDER_HOSTS = {"example.com", "example.org", "example.net", "placeholder.com"}
PLACEHOLDER_PART = re.compile(
    r"(?:^|[./_-])(?:your[-_]?(?:username|user|repo|repository|org|organization)|"
    r"username|placeholder|replace[-_]?me|todo|tbd)(?:$|[./_-])",
    re.IGNORECASE,
)
GITHUB_PLACEHOLDER = re.compile(
    r"^/(?:owner|user|org)/(?:repo|repository)(?:/|$)", re.IGNORECASE
)


class Page(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids: set[str] = set()
        self.references: list[tuple[int, str]] = []
        self.base_tags: list[int] = []
        self.in_style = False

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        attrs = dict(attributes)
        if tag == "base":
            self.base_tags.append(self.getpos()[0])
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.ids.add(attrs["name"])
        for name in ("href", "src"):
            if name in attrs:
                self.references.append((self.getpos()[0], attrs[name] or ""))
        if attrs.get("style"):
            self.add_css(attrs["style"], self.getpos()[0])
        if tag == "style":
            self.in_style = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag == "style":
            self.in_style = False

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_style:
            self.add_css(data, self.getpos()[0])

    def add_css(self, css: str, start_line: int) -> None:
        for match in CSS_URL.finditer(CSS_COMMENT.sub("", css)):
            line = start_line + css[: match.start()].count("\n")
            self.references.append((line, match.group(2)))


def main() -> int:
    if len(sys.argv) > 2:
        print(__doc__)
        return 2
    repo = Path(__file__).resolve().parents[1]
    site = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else repo / "docs"
    if not site.is_dir():
        print(f"FAIL: website directory does not exist: {site}")
        return 1
    pages: dict[Path, Page] = {}
    errors: list[str] = []
    checked = 0

    def label(path: Path) -> str:
        try:
            return str(path.relative_to(repo))
        except ValueError:
            return str(path)

    def fail(path: Path, line: int, message: str) -> None:
        errors.append(f"{label(path)}:{line}: {message}")

    for path in sorted(path for path in site.rglob("*") if path.suffix.lower() in {".html", ".htm"}):
        path = path.resolve()
        page = Page(path)
        page.feed(path.read_text(encoding="utf-8"))
        page.close()
        pages[path] = page
        for line in page.base_tags:
            fail(path, line, "<base> changes URL resolution; use explicit relative links")

    if not pages:
        errors.append(f"{label(site)}: no HTML pages found")

    def check(source: Path, line: int, raw_url: str) -> None:
        nonlocal checked
        checked += 1
        url = raw_url.strip()
        if not url or url == "#":
            fail(source, line, f"empty or dangling link: {raw_url!r}")
            return
        try:
            parsed = urlsplit(url)
        except ValueError:
            fail(source, line, f"malformed URL: {url!r}")
            return
        if parsed.scheme in {"data", "mailto", "tel"}:
            return
        if parsed.scheme in {"http", "https"} or parsed.netloc:
            hostname = (parsed.hostname or "").lower()
            if not hostname:
                fail(source, line, f"URL has no hostname: {url!r}")
            elif (
                any(hostname == host or hostname.endswith("." + host) for host in PLACEHOLDER_HOSTS)
                or PLACEHOLDER_PART.search(unquote(parsed.netloc + parsed.path))
                or (hostname == "github.com" and GITHUB_PLACEHOLDER.search(unquote(parsed.path)))
                or "<" in unquote(url)
                or ">" in unquote(url)
            ):
                fail(source, line, f"placeholder external URL: {url!r}")
            return
        if parsed.scheme:
            fail(source, line, f"unsupported URL scheme: {url!r}")
            return
        if parsed.path.startswith("/"):
            fail(source, line, f"root-relative link is unsafe for a Pages project path: {url!r}")
            return

        target = (source.parent / unquote(parsed.path)).resolve() if parsed.path else source
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            fail(source, line, f"missing target: {url!r} -> {label(target)}")
            return
        fragment = unquote(parsed.fragment)
        if fragment and target.suffix.lower() in {".html", ".htm"}:
            if target not in pages:
                page = Page(target)
                page.feed(target.read_text(encoding="utf-8"))
                page.close()
                pages[target] = page
            if fragment not in pages[target].ids:
                fail(source, line, f"missing fragment: {url!r}")

    for path, page in list(pages.items()):
        for line, url in page.references:
            check(path, line, url)
    css_files = sorted(site.rglob("*.css"))
    for path in css_files:
        css = path.read_text(encoding="utf-8")
        for match in CSS_URL.finditer(CSS_COMMENT.sub("", css)):
            check(path, css[: match.start()].count("\n") + 1, match.group(2))

    if errors:
        print("FAIL: website reference validation")
        for error in errors:
            print(f"  {error}")
        return 1
    print(f"PASS: {checked} references across {len(pages)} HTML files and {len(css_files)} CSS files")
    print("External URLs were screened for placeholders; HTTP availability was not checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
