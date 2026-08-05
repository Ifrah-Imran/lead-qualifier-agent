"""Website fetching helpers for /enrich — requests + BeautifulSoup."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PAGE_TIMEOUT_SECONDS = 5
MAX_EXTRA_PAGES = 2
MAX_TEXT_CHARS = 12_000

LINK_KEYWORDS = ("about", "team", "company", "careers", "contact")

# A UA string alone isn't enough for some bot-protection (e.g. Cloudflare) —
# it also checks for the Accept/Accept-Language headers a real browser sends.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def normalize_url(url: str) -> str:
    """Ensure the URL has a scheme so requests can fetch it."""
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"https://{url}"
    return url


def fetch_html(url: str) -> Optional[str]:
    """Fetch a page. Returns HTML text, or None on timeout/error (never raises)."""
    try:
        response = requests.get(
            url,
            timeout=PAGE_TIMEOUT_SECONDS,
            headers=_HEADERS,
            allow_redirects=True,
        )
        response.raise_for_status()
        return response.text
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        logger.warning("fetch_html: %s returned HTTP %s", url, status)
        return None
    except (requests.RequestException, ValueError) as exc:
        logger.warning("fetch_html: %s failed — %s: %s", url, type(exc).__name__, exc)
        return None


def visible_text(html: str) -> str:
    """Strip scripts/styles and return readable page text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def find_related_links(html: str, base_url: str, limit: int = MAX_EXTRA_PAGES) -> list[str]:
    """Find up to `limit` same-site links whose URL or label mentions ICP-ish pages."""
    soup = BeautifulSoup(html, "html.parser")
    base_host = urlparse(base_url).netloc.lower()
    found: list[str] = []
    seen: set[str] = {base_url.rstrip("/").lower()}

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc.lower() != base_host:
            continue

        label = anchor.get_text(" ", strip=True).lower()
        path = parsed.path.lower()
        haystack = f"{path} {label}"
        if not any(keyword in haystack for keyword in LINK_KEYWORDS):
            continue

        normalized = absolute.split("#")[0].rstrip("/")
        key = normalized.lower()
        if key in seen:
            continue

        seen.add(key)
        found.append(normalized)
        if len(found) >= limit:
            break

    return found


def gather_company_text(website_url: str) -> tuple[str, list[str]]:
    """
    Fetch homepage + up to 2 related pages.
    Returns (combined_visible_text, list_of_urls_successfully_fetched).
    Failed pages are skipped — this never raises.
    """
    homepage = normalize_url(website_url)
    fetched_urls: list[str] = []
    chunks: list[str] = []

    homepage_html = fetch_html(homepage)
    if homepage_html:
        fetched_urls.append(homepage)
        chunks.append(visible_text(homepage_html))
        related = find_related_links(homepage_html, homepage)
    else:
        related = []

    for url in related:
        html = fetch_html(url)
        if not html:
            continue
        fetched_urls.append(url)
        chunks.append(visible_text(html))

    combined = "\n\n".join(chunk for chunk in chunks if chunk)
    if len(combined) > MAX_TEXT_CHARS:
        combined = combined[:MAX_TEXT_CHARS]

    return combined, fetched_urls
