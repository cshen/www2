#!/usr/bin/env python3
"""
fetch_abstracts_arxiv.py — Pass 1: fetch abstracts by scraping arxiv.org HTML pages.

Uses the human-facing https://arxiv.org/abs/<id> pages (BeautifulSoup) instead of
the export API, which avoids the strict API rate limits.

Run this first to populate abstract/<key>.txt for all papers with an `eprint` field.
Then run fetch_abstracts.py (SKIP_EXISTING=True) for papers without arXiv IDs.

Usage:
    pip install requests beautifulsoup4 bibtexparser
    python3 fetch_abstracts_arxiv.py
"""

import bibtexparser
import requests
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup

BIB_FILE     = "cs.bib"
ABSTRACT_DIR = Path("abstract")
SUMMARY_FILE = ABSTRACT_DIR / "_summary.txt"
ARXIV_ABS    = "https://arxiv.org/abs/{}"
DELAY        = 2.0   # seconds between page fetches (polite crawling)
HEADERS      = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

ABSTRACT_DIR.mkdir(exist_ok=True)


def slug(eid):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", eid)


def fetch_arxiv_html(eprint):
    """Scrape the abstract from https://arxiv.org/abs/<eprint>."""
    url = ARXIV_ABS.format(eprint.strip())
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f"  [rate-limited] sleeping {wait}s …", flush=True)
                time.sleep(wait)
                continue
            if resp.status_code == 404:
                return None   # paper not on arXiv
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            # Primary: <blockquote class="abstract mathjax">
            block = soup.find("blockquote", class_="abstract")
            if block:
                # Remove the "Abstract:" label span
                for span in block.find_all("span", class_="descriptor"):
                    span.decompose()
                text = block.get_text(separator=" ", strip=True)
                return re.sub(r"\s+", " ", text).strip()

            # Fallback: <meta name="citation_abstract">
            meta = soup.find("meta", attrs={"name": "citation_abstract"})
            if meta and meta.get("content"):
                return re.sub(r"\s+", " ", meta["content"].strip())

            return None   # page loaded but no abstract found

        except Exception as exc:
            print(f"  [error attempt {attempt+1}] {exc}", flush=True)
            time.sleep(10)
    return None


def main():
    print(f"Loading {BIB_FILE} …", flush=True)
    with open(BIB_FILE, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    entries = db.entries
    print(f"  {len(entries)} entries found.\n", flush=True)

    skipped   = []
    no_eprint = []
    found     = []
    failed    = []

    to_fetch = []
    for entry in entries:
        key    = entry.get("ID", "")
        eprint = entry.get("eprint", "").strip()
        out    = ABSTRACT_DIR / f"{slug(key)}.txt"
        if out.exists():
            skipped.append(key)
        elif not eprint:
            no_eprint.append(key)
        else:
            to_fetch.append((key, eprint))

    print(f"  Already have  : {len(skipped)}")
    print(f"  To fetch      : {len(to_fetch)} (scraping arxiv.org/abs/<id>)")
    print(f"  No eprint     : {len(no_eprint)} (will need Semantic Scholar / OpenAlex pass)\n",
          flush=True)

    for i, (key, eprint) in enumerate(to_fetch, 1):
        print(f"[{i:3d}/{len(to_fetch)}] {key}  ({eprint}) … ", end="", flush=True)
        abstract = fetch_arxiv_html(eprint)

        if abstract:
            (ABSTRACT_DIR / f"{slug(key)}.txt").write_text(abstract, encoding="utf-8")
            found.append((key, eprint))
            print(f"✓  {len(abstract)} chars", flush=True)
        else:
            failed.append((key, eprint))
            print("✗  not found", flush=True)

        if i < len(to_fetch):
            time.sleep(DELAY)

    # ── summary ───────────────────────────────────────────────────────────────
    lines = [
        "Abstract Fetch Summary — arXiv HTML scrape pass",
        "=" * 60,
        f"Total entries         : {len(entries)}",
        f"Already existed       : {len(skipped)}",
        f"Fetched via arXiv     : {len(found)}",
        f"eprint but not found  : {len(failed)}",
        f"No eprint (need S2)   : {len(no_eprint)}",
        "",
    ]
    if failed:
        lines += ["EPRINT BUT NOT FOUND ON ARXIV", "-" * 60]
        lines += [f"  {k:45s}  eprint={ep}" for k, ep in failed]
        lines.append("")
    if no_eprint:
        lines += ["NO EPRINT — NEEDS SEMANTIC SCHOLAR / OPENALEX PASS", "-" * 60]
        lines += [f"  {k}" for k in no_eprint]
        lines.append("")

    SUMMARY_FILE.write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "=" * 60, flush=True)
    print(f"Done: {len(found)} fetched, {len(failed)} not found, "
          f"{len(no_eprint)} need S2/OpenAlex pass.", flush=True)
    print(f"Summary → {SUMMARY_FILE}")
    print("Next: python3 fetch_abstracts.py   (SKIP_EXISTING=True)")


if __name__ == "__main__":
    main()
