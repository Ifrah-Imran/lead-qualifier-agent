"""Website fetching helpers for /enrich — requests + BeautifulSoup."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PAGE_TIMEOUT_SECONDS = 5
MAX_EXTRA_PAGES = 2
MAX_TEXT_CHARS = 12_000

LINK_KEYWORDS = ("about", "team", "company", "careers", "contact")

# Requires a separator between digit groups (space/dash/dot/parens) to avoid
# matching arbitrary unbroken digit runs (order IDs, zip+4, etc.) — trades
# missing unformatted numbers like "5551234567" for fewer false positives.
PHONE_PATTERN = re.compile(r"\+?\d{1,3}?[-.\s]?\(?\d{2,4}\)?[-.\s]\d{3,4}[-.\s]?\d{3,4}")

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# "logo@2x.png" / "photo@3x.jpg" (retina-image naming) match the email shape —
# excluded by TLD since a real address never ends in an image extension.
_EMAIL_TLD_EXCLUDE = {"png", "jpg", "jpeg", "gif", "svg", "webp", "ico"}

SOCIAL_DOMAINS: dict[str, tuple[str, ...]] = {
    "linkedin": ("linkedin.com",),
    "instagram": ("instagram.com",),
    "facebook": ("facebook.com", "fb.com"),
    "twitter": ("twitter.com", "x.com"),
}


@dataclass
class ScrapeResult:
    text: str
    source_urls: list[str] = field(default_factory=list)
    phone: Optional[str] = None
    email: Optional[str] = None
    social_links: dict[str, str] = field(default_factory=dict)
    reachable: bool = True
    fetch_error: Optional[str] = None

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


def _describe_fetch_error(exc: Exception) -> str:
    """Map a request failure to a short, human-readable reason."""
    if isinstance(exc, requests.exceptions.SSLError):
        return "SSL certificate error"
    if isinstance(exc, requests.exceptions.Timeout):
        return f"timed out after {PAGE_TIMEOUT_SECONDS}s"
    if isinstance(exc, requests.exceptions.ConnectionError):
        if "NameResolutionError" in str(exc) or "getaddrinfo failed" in str(exc):
            return "domain does not resolve (DNS failure)"
        return "could not connect"
    return "failed to load"


def fetch_html(url: str) -> tuple[Optional[str], Optional[str]]:
    """Fetch a page. Returns (html, None) on success, or (None, reason) on
    timeout/DNS/SSL/HTTP error — never raises."""
    try:
        response = requests.get(
            url,
            timeout=PAGE_TIMEOUT_SECONDS,
            headers=_HEADERS,
            allow_redirects=True,
        )
        response.raise_for_status()
        return response.text, None
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        logger.warning("fetch_html: %s returned HTTP %s", url, status)
        return None, f"site returned HTTP {status}"
    except (requests.RequestException, ValueError) as exc:
        logger.warning("fetch_html: %s failed — %s: %s", url, type(exc).__name__, exc)
        return None, _describe_fetch_error(exc)


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


def find_phone(text: str) -> Optional[str]:
    """Best-effort: first plausible-looking phone number in visible page text."""
    for match in PHONE_PATTERN.finditer(text):
        candidate = match.group().strip()
        digit_count = sum(c.isdigit() for c in candidate)
        if 7 <= digit_count <= 15:
            return candidate
    return None


def _plausible_email(candidate: str) -> bool:
    tld = candidate.rsplit(".", 1)[-1].lower()
    return tld not in _EMAIL_TLD_EXCLUDE


def find_email(text: str, html: str) -> Optional[str]:
    """Best-effort: prefer a mailto: link (most reliable), fall back to the
    first plausible-looking email address in visible page text."""
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if href.lower().startswith("mailto:"):
            address = href[len("mailto:"):].split("?")[0].strip()
            if address and _plausible_email(address):
                return address

    for match in EMAIL_PATTERN.finditer(text):
        candidate = match.group()
        if _plausible_email(candidate):
            return candidate
    return None


def find_social_links(html: str) -> dict[str, str]:
    """Scan <a href> tags for links to known social platforms."""
    soup = BeautifulSoup(html, "html.parser")
    found: dict[str, str] = {}
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href:
            continue
        host = urlparse(href).netloc.lower()
        if not host:
            continue
        for platform, domains in SOCIAL_DOMAINS.items():
            if platform in found:
                continue
            if any(host == d or host.endswith(f".{d}") for d in domains):
                found[platform] = href
    return found


def gather_company_text(website_url: str) -> ScrapeResult:
    """
    Fetch homepage + up to 2 related pages.
    Extracts visible text, a best-effort phone number, email address, and
    social profile links from the same pages — no extra HTTP requests beyond
    what enrichment already fetches. Failed pages are skipped — this never
    raises. `reachable` / `fetch_error` reflect only the homepage fetch, since
    that's the one request that must succeed for enrichment to mean anything;
    related-page failures are silently best-effort.
    """
    homepage = normalize_url(website_url)
    fetched_urls: list[str] = []
    chunks: list[str] = []
    phone: Optional[str] = None
    email: Optional[str] = None
    social_links: dict[str, str] = {}

    def process_page(html: str) -> None:
        nonlocal phone, email
        text = visible_text(html)
        chunks.append(text)
        if phone is None:
            phone = find_phone(text)
        if email is None:
            email = find_email(text, html)
        for platform, url in find_social_links(html).items():
            social_links.setdefault(platform, url)

    homepage_html, fetch_error = fetch_html(homepage)
    if homepage_html:
        fetched_urls.append(homepage)
        process_page(homepage_html)
        related = find_related_links(homepage_html, homepage)
    else:
        related = []

    for url in related:
        html, _related_error = fetch_html(url)
        if not html:
            continue
        fetched_urls.append(url)
        process_page(html)

    combined = "\n\n".join(chunk for chunk in chunks if chunk)
    if len(combined) > MAX_TEXT_CHARS:
        combined = combined[:MAX_TEXT_CHARS]

    return ScrapeResult(
        text=combined,
        source_urls=fetched_urls,
        phone=phone,
        email=email,
        social_links=social_links,
        reachable=homepage_html is not None,
        fetch_error=fetch_error,
    )
