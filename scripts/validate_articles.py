#!/usr/bin/env python3
"""
validate_articles.py
---------------------------------------------------------------------------
Validates every article JSON under data/articles/<YYYY-MM-DD>/*.json against
data/articles/schema.json before the site gets built.

Run this as a gate in the daily pipeline, right after articles are written
and right before scripts/build_site.py runs:

    python3 scripts/validate_articles.py

Exit code 0  -> every article is valid, safe to build.
Exit code 1  -> at least one article failed validation; the printed report
                says exactly which file and which rule. Do NOT run
                build_site.py against invalid data.

Also usable as a library:

    from scripts.validate_articles import validate_all
    ok, results = validate_all(Path("data/articles"))
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover
    print(
        "[validate_articles] Missing dependency 'jsonschema'.\n"
        "Install it with: pip install jsonschema\n"
        "(it's listed in requirements.txt)",
        file=sys.stderr,
    )
    sys.exit(2)


def find_project_root(start: Path) -> Path:
    """Walk up from `start` until a directory containing data/articles is found."""
    for candidate in [start, *start.parents]:
        if (candidate / "data" / "articles").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate a 'data/articles' directory above "
        f"{start} — run this from within the project."
    )


def validate_all(articles_dir: Path) -> tuple[bool, list[dict]]:
    """
    Validate every *.json file under articles_dir/<date>/ against
    articles_dir/schema.json.

    Returns (all_ok, results) where results is a list of
    {"path": str, "ok": bool, "errors": list[str]}.
    """
    schema_path = articles_dir / "schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    validator = jsonschema.Draft7Validator(schema)
    results: list[dict] = []
    all_ok = True

    date_dirs = sorted(p for p in articles_dir.iterdir() if p.is_dir())
    for date_dir in date_dirs:
        for article_path in sorted(date_dir.glob("*.json")):
            errors: list[str] = []
            try:
                data = json.loads(article_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"invalid JSON: {e}")
                data = None

            if data is not None:
                for err in sorted(
                    validator.iter_errors(data), key=lambda e: list(e.path)
                ):
                    loc = "/".join(str(p) for p in err.path) or "<root>"
                    errors.append(f"{loc}: {err.message}")

            ok = not errors
            all_ok = all_ok and ok
            results.append(
                {"path": str(article_path), "ok": ok, "errors": errors}
            )

    return all_ok, results


def main() -> int:
    start = Path.cwd()
    try:
        root = find_project_root(start)
    except FileNotFoundError as e:
        print(f"[validate_articles] {e}", file=sys.stderr)
        return 2

    articles_dir = root / "data" / "articles"
    all_ok, results = validate_all(articles_dir)

    if not results:
        print("[validate_articles] No article JSON files found — nothing to validate.")
        return 0

    for r in results:
        rel = Path(r["path"]).relative_to(root)
        if r["ok"]:
            print(f"  OK    {rel}")
        else:
            print(f"  FAIL  {rel}")
            for err in r["errors"]:
                print(f"          - {err}")

    passed = sum(1 for r in results if r["ok"])
    failed = len(results) - passed
    print(f"\n[validate_articles] {passed} passed, {failed} failed, {len(results)} total.")

    if not all_ok:
        print(
            "[validate_articles] FAILED — fix the article(s) above before "
            "running build_site.py.",
            file=sys.stderr,
        )
        return 1

    print("[validate_articles] All articles valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
