#!/usr/bin/env python3
"""Fetch a researcher's works from OpenAlex by ORCID.

Writes papers.json (full detail, used to build the page) and papers.xlsx
(a skimmable list for checking the results by eye).

Usage:
    python3 fetch_papers.py [ORCID]
"""

import json
import sys
import time

import requests
from openpyxl import Workbook

ORCID = sys.argv[1] if len(sys.argv) > 1 else "0000-0001-7001-2275"
API = "https://api.openalex.org/works"
# OpenAlex asks for an email in the UA string; it gets you the faster pool.
HEADERS = {"User-Agent": "MyPublications/1.0 (mailto:gtsambos@uw.edu)"}


def get(params, attempts=5):
    """GET with backoff. OpenAlex rate-limits, so retry rather than fail."""
    for i in range(attempts):
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 503):
            wait = 2 ** i
            print(f"  rate-limited ({r.status_code}), waiting {wait}s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
    raise RuntimeError(f"giving up after {attempts} attempts")


def fetch(orcid):
    works, cursor = [], "*"
    while cursor:
        data = get({
            "filter": f"author.orcid:{orcid}",
            "per-page": 200,
            "cursor": cursor,
        })
        works.extend(data["results"])
        cursor = data["meta"].get("next_cursor")
        print(f"  fetched {len(works)}/{data['meta']['count']}")
    return works


def simplify(w):
    """Keep only what the page needs."""
    loc = (w.get("primary_location") or {}).get("source") or {}
    return {
        "id": w.get("id"),
        "title": w.get("display_name"),
        "year": w.get("publication_year"),
        "date": w.get("publication_date"),
        "venue": loc.get("display_name"),
        "type": w.get("type"),
        "doi": w.get("doi"),
        "url": w.get("doi") or (w.get("primary_location") or {}).get("landing_page_url"),
        "cited_by_count": w.get("cited_by_count", 0),
        "counts_by_year": {
            c["year"]: c["cited_by_count"] for c in w.get("counts_by_year", [])
        },
        "authors": [
            a["author"]["display_name"] for a in w.get("authorships", [])
        ],
        "is_retracted": w.get("is_retracted", False),
    }


def apply_exclusions(papers):
    """Apply the by-eye checking decisions recorded in exclusions.json."""
    try:
        with open("exclusions.json", encoding="utf-8") as f:
            rules = json.load(f)
    except FileNotFoundError:
        print("  no exclusions.json — keeping everything")
        return papers

    keep_types = rules.get("keep_types") or []
    excluded_ids = rules.get("excluded_ids") or {}
    kept = [
        p for p in papers
        if (not keep_types or p["type"] in keep_types)
        and p["id"] not in excluded_ids
    ]
    print(f"  exclusions: {len(papers)} -> {len(kept)} works")
    return kept


def main():
    print(f"Fetching works for ORCID {ORCID}")
    papers = [simplify(w) for w in fetch(ORCID)]
    papers.sort(key=lambda p: (p["year"] or 0, p["title"] or ""), reverse=True)

    with open("papers_all.json", "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    papers = apply_exclusions(papers)

    with open("papers.json", "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    wb = Workbook()
    ws = wb.active
    ws.title = "papers"
    ws.append(["#", "Year", "Title", "Venue", "Type", "Citations", "Co-authors"])
    for i, p in enumerate(papers, 1):
        others = [a for a in p["authors"] if "Tsambos" not in a]
        ws.append([
            i, p["year"], p["title"], p["venue"], p["type"],
            p["cited_by_count"], ", ".join(others[:8]),
        ])
    for col, width in zip("ABCDEFG", [5, 7, 70, 35, 14, 11, 60]):
        ws.column_dimensions[col].width = width
    wb.save("papers.xlsx")

    print(f"\n{len(papers)} works -> papers.json, papers.xlsx")
    by_type = {}
    for p in papers:
        by_type[p["type"]] = by_type.get(p["type"], 0) + 1
    print("\nBy type:")
    for t, n in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print(f"  {t:<16} {n}")
    total = sum(p["cited_by_count"] for p in papers)
    years = [p["year"] for p in papers if p["year"]]
    if years:
        print(f"\nYears: {min(years)}-{max(years)}   Total citations: {total}")


if __name__ == "__main__":
    main()
