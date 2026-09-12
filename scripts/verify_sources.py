#!/usr/bin/env python3
"""
verify_sources.py
---------------------------------------------------------------------------
Checks that every `sources[].url` in the article JSON actually resolves.

Schema validation only proves an article is shaped correctly. It cannot tell
you the cited URL was invented, or that a link has rotted since publication.
This script fetches each distinct source URL and reports the ones that are
provably gone.

    python3 scripts/verify_sources.py
    python3 scripts/verify_sources.py --warn-only      # never fail the build
    python3 scripts/verify_sources.py --date 2026-06-13

Exit code 0  -> no dead links (or --warn-only was passed).
Exit code 1  -> at least one source URL is provably dead.
Exit code 2  -> the script could not run (bad path, etc).

Outcomes are graded, because "not 200" does not mean "not real":

    DEAD          404/410, DNS failure, refused connection -> hard failure.
    UNVERIFIED    401/403/429, timeouts, TLS errors -> warning only. Plenty of
                  real sites block datacenter IPs or HEAD requests, and failing
                  the daily build on those would make CI useless.
    OK            any 2xx/3xx after redirects.

Also usable as a library:

    from scripts.verify_sources import verify_all
    ok, results = verify_all(Path("data/articles"))
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

# Many publishers reject the default python-urllib agent outright.
USER_AGENT = (
    "Mozilla/5.0 (compatible; TechPulseLinkCheck/1.0; "
    "+https://github.com/boon-boon/Daily-AI-Tech-News-Blog-Automation)"
)

OK = "OK"
DEAD = "DEAD"
UNVERIFIED = "UNVERIFIED"

DEAD_STATUSES = {404, 410}


def find_project_root(start: Path) -> Path:
    """Walk up from `start` until a directory containing data/articles is found."""
    for candidate in [start, *start.parents]:
        if (candidate / "data" / "articles").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate a 'data/articles' directory above "
        f"{start} — run this from within the project."
    )


def collect_sources(articles_dir: Path, date: str | None = None) -> dict[str, list[str]]:
    """Map each distinct source URL -> the article paths citing it."""
    citations: dict[str, list[str]] = {}

    date_dirs = sorted(p for p in articles_dir.iterdir() if p.is_dir())
    if date:
        date_dirs = [p for p in date_dirs if p.name == date]

    for date_dir in date_dirs:
        for article_path in sorted(date_dir.glob("*.json")):
            try:
                data = json.loads(article_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                # validate_articles.py is the gate for malformed JSON; skip here.
                continue
            for source in data.get("sources") or []:
                url = (source or {}).get("url")
                if isinstance(url, str) and url.strip():
                    citations.setdefault(url.strip(), []).append(str(article_path))

    return citations


def check_url(url: str, timeout: float = 10.0) -> tuple[str, str]:
    """Fetch `url` and grade it. Returns (status, detail)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return DEAD, f"unsupported scheme {parsed.scheme!r}"
    if not parsed.netloc:
        return DEAD, "no host in URL"

    # HEAD is cheaper, but a fair number of hosts answer it with 403/405/501
    # while serving GET fine — so fall back rather than trusting the refusal.
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(
            url, method=method, headers={"User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return OK, f"{method} {resp.status}"
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):
                continue
            if e.code in DEAD_STATUSES:
                return DEAD, f"{method} {e.code}"
            return UNVERIFIED, f"{method} {e.code}"
        except urllib.error.URLError as e:
            reason = e.reason
            if isinstance(reason, socket.gaierror):
                return DEAD, f"DNS lookup failed for {parsed.netloc}"
            if isinstance(reason, ConnectionRefusedError):
                return DEAD, f"connection refused by {parsed.netloc}"
            return UNVERIFIED, f"unreachable: {reason}"
        except (TimeoutError, socket.timeout):
            return UNVERIFIED, f"timed out after {timeout:g}s"
        except Exception as e:  # noqa: BLE001 - a link check must never crash the build
            return UNVERIFIED, f"{type(e).__name__}: {e}"

    return UNVERIFIED, "no response"


def verify_all(
    articles_dir: Path,
    date: str | None = None,
    timeout: float = 10.0,
    jobs: int = 8,
) -> tuple[bool, list[dict]]:
    """
    Check every distinct source URL under articles_dir.

    Returns (no_dead_links, results) where results is a list of
    {"url": str, "status": str, "detail": str, "articles": list[str]}.
    """
    citations = collect_sources(articles_dir, date)
    if not citations:
        return True, []

    urls = list(citations)
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        graded = list(pool.map(lambda u: check_url(u, timeout), urls))

    results = [
        {
            "url": url,
            "status": status,
            "detail": detail,
            "articles": citations[url],
        }
        for url, (status, detail) in zip(urls, graded)
    ]
    results.sort(key=lambda r: ({DEAD: 0, UNVERIFIED: 1, OK: 2}[r["status"]], r["url"]))

    no_dead = not any(r["status"] == DEAD for r in results)
    return no_dead, results


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify article source URLs resolve.")
    parser.add_argument("--date", help="Only check one date folder, e.g. 2026-06-13.")
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="Per-request timeout in seconds."
    )
    parser.add_argument(
        "--jobs", type=int, default=8, help="Parallel requests (default 8)."
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Report dead links but always exit 0.",
    )
    args = parser.parse_args()

    try:
        root = find_project_root(Path.cwd())
    except FileNotFoundError as e:
        print(f"[verify_sources] {e}", file=sys.stderr)
        return 2

    articles_dir = root / "data" / "articles"
    no_dead, results = verify_all(
        articles_dir, date=args.date, timeout=args.timeout, jobs=args.jobs
    )

    if not results:
        print("[verify_sources] No source URLs found — nothing to check.")
        return 0

    for r in results:
        print(f"  {r['status']:<10} {r['url']}  ({r['detail']})")
        if r["status"] != OK:
            for a in r["articles"]:
                print(f"               cited by {Path(a).relative_to(root)}")

    counts = {s: sum(1 for r in results if r["status"] == s) for s in (OK, UNVERIFIED, DEAD)}
    print(
        f"\n[verify_sources] {counts[OK]} ok, {counts[UNVERIFIED]} unverified, "
        f"{counts[DEAD]} dead, {len(results)} total."
    )

    if counts[UNVERIFIED]:
        print(
            "[verify_sources] Unverified links are not failures — the host blocked "
            "or timed out on an automated request. Spot-check them by hand."
        )

    if not no_dead:
        if args.warn_only:
            print("[verify_sources] Dead links found (--warn-only, not failing).")
            return 0
        print(
            "[verify_sources] FAILED — the dead source(s) above must be corrected "
            "or removed before publishing.",
            file=sys.stderr,
        )
        return 1

    print("[verify_sources] No dead source links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
