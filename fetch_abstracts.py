#!/usr/bin/env python3
"""
fetch_abstracts.py — Fetch abstracts for all papers in cs.bib.

Strategy (tried in order for each paper):
  1. arXiv HTML scrape — scrapes https://arxiv.org/abs/<eprint> (when eprint present)
  2. Semantic Scholar  — title + first-author search via free public API
  3. OpenAlex          — free academic API, no auth needed (good fallback)
  4. Google Scholar    — fallback via `scholarly` (slow, may be rate-limited)

Output:
  abstract/<key>.txt        — one file per paper (plain text)
  abstract/_summary.txt     — found / not-found report

Usage:
  pip install bibtexparser requests beautifulsoup4 scholarly
  python3 fetch_abstracts.py

Options (edit the CONFIG block below):
  SKIP_EXISTING   — skip keys whose .txt already exists (default: True)
  USE_SEMANTIC_S2 — enable Semantic Scholar source (default: True)
  USE_OPENALEX    — enable OpenAlex source (default: True)
  USE_SCHOLARLY   — enable Google Scholar fallback (slower; default: True)
  S2_API_KEY      — optional free key from semanticscholar.org/product/api
"""

import bibtexparser
import requests
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup

# ── CONFIG ────────────────────────────────────────────────────────────────────
BIB_FILE       = "cs.bib"
ABSTRACT_DIR   = Path("abstract")
SUMMARY_FILE   = ABSTRACT_DIR / "_summary.txt"
SKIP_EXISTING  = True    # set False to re-fetch everything
USE_SEMANTIC_S2 = False  # set False to skip Semantic Scholar (e.g. when IP is throttled)
USE_OPENALEX   = True    # OpenAlex free API — good fallback, no auth needed
USE_SCHOLARLY  = True    # Google Scholar via `scholarly` — slow, last resort
S2_API_KEY     = ""      # optional: free key from semanticscholar.org/product/api
DELAY_ARXIV    = 2.0     # seconds between arXiv HTML page fetches
DELAY_S2       = 4.0     # seconds between Semantic Scholar requests
DELAY_OPENALEX = 1.0     # seconds between OpenAlex requests (generous free tier)
DELAY_SCHOLAR  = 8.0     # seconds between Google Scholar requests
# ─────────────────────────────────────────────────────────────────────────────

ARXIV_ABS  = "https://arxiv.org/abs/{}"
S2_API     = "https://api.semanticscholar.org/graph/v1/paper/search"
OA_API     = "https://api.openalex.org/works"
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
BOT_UA = "AbstractFetcher/1.0 (academic-research-tool; mailto:research@example.com)"

ABSTRACT_DIR.mkdir(exist_ok=True)


# ── helpers ───────────────────────────────────────────────────────────────────

def clean_latex(s):
    """Strip LaTeX markup to get a plain-text string suitable for search."""
    if not s:
        return ""
    s = re.sub(r"\$[^$]+\$", " ", s)
    s = re.sub(r"\\text[a-z]+\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    s = re.sub(r"[{}\\]", " ", s)
    s = s.replace("---", " ").replace("--", " ")
    return re.sub(r"\s+", " ", s).strip()


def first_author_last(raw_author):
    """Return last name of the first author from a BibTeX author field."""
    if not raw_author:
        return ""
    first = re.split(r"\s+and\s+", raw_author.strip(), maxsplit=1)[0].strip()
    if "," in first:
        return clean_latex(first.split(",")[0].strip())
    parts = clean_latex(first).split()
    return parts[-1] if parts else ""


def slug(eid):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", eid)


def title_overlap(query_title, candidate_title, threshold=0.6):
    """True if ≥threshold of the query's long words appear in the candidate."""
    qw = set(re.findall(r"[a-z]{4,}", query_title.lower()))
    cw = set(re.findall(r"[a-z]{4,}", candidate_title.lower()))
    return bool(qw) and len(qw & cw) / len(qw) >= threshold


# ── source 1: arXiv HTML scrape ───────────────────────────────────────────────

def fetch_arxiv_html(eprint):
    """Scrape abstract from https://arxiv.org/abs/<eprint>. No API key needed."""
    eprint = eprint.strip()
    if not eprint:
        return None
    url = ARXIV_ABS.format(eprint)
    for attempt in range(3):
        try:
            resp = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=15)
            if resp.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f"        [arXiv] rate-limited, sleeping {wait}s …")
                time.sleep(wait)
                continue
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            block = soup.find("blockquote", class_="abstract")
            if block:
                for span in block.find_all("span", class_="descriptor"):
                    span.decompose()
                return re.sub(r"\s+", " ", block.get_text(separator=" ", strip=True))
            meta = soup.find("meta", attrs={"name": "citation_abstract"})
            if meta and meta.get("content"):
                return re.sub(r"\s+", " ", meta["content"].strip())
        except Exception as exc:
            print(f"        [arXiv] error (attempt {attempt+1}): {exc}")
            time.sleep(10)
    return None


# ── source 2: Semantic Scholar API ───────────────────────────────────────────

def fetch_semantic_scholar(title, first_author_last_name):
    """Search Semantic Scholar API and return the abstract of the best match."""
    query = f"{title} {first_author_last_name}".strip()
    hdrs  = {"User-Agent": BOT_UA}
    if S2_API_KEY:
        hdrs["x-api-key"] = S2_API_KEY
    try:
        resp = requests.get(
            S2_API,
            params={"query": query, "fields": "title,abstract", "limit": 3},
            headers=hdrs,
            timeout=20,
        )
        if resp.status_code == 429:
            wait = 120
            print(f"        [S2] rate-limited, sleeping {wait}s then one retry …")
            time.sleep(wait)
            resp = requests.get(
                S2_API,
                params={"query": query, "fields": "title,abstract", "limit": 3},
                headers=hdrs, timeout=20,
            )
            if resp.status_code == 429:
                print("        [S2] still rate-limited — skipping.")
                return None
        resp.raise_for_status()
        for paper in resp.json().get("data", []):
            if title_overlap(title, paper.get("title") or ""):
                abstract = (paper.get("abstract") or "").strip()
                if abstract:
                    return re.sub(r"\s+", " ", abstract)
    except Exception as exc:
        print(f"        [S2] error: {exc}")
    return None


# ── source 3: OpenAlex API ────────────────────────────────────────────────────

def fetch_openalex(title):
    """Search OpenAlex (free, no auth) and reconstruct abstract from inverted index."""
    try:
        resp = requests.get(
            OA_API,
            params={"search": title, "per-page": 3, "select": "title,abstract_inverted_index"},
            headers={"User-Agent": BOT_UA},
            timeout=15,
        )
        resp.raise_for_status()
        for work in resp.json().get("results", []):
            if not title_overlap(title, work.get("title") or ""):
                continue
            inv = work.get("abstract_inverted_index") or {}
            if not inv:
                continue
            # Reconstruct abstract from inverted index: {word: [positions]}
            max_pos = max(pos for positions in inv.values() for pos in positions)
            words = [""] * (max_pos + 1)
            for word, positions in inv.items():
                for pos in positions:
                    words[pos] = word
            abstract = re.sub(r"\s+", " ", " ".join(words).strip())
            if abstract:
                return abstract
    except Exception as exc:
        print(f"        [OpenAlex] error: {exc}")
    return None


# ── source 4: Google Scholar (scholarly) ──────────────────────────────────────

_scholarly_available = False
if USE_SCHOLARLY:
    try:
        from scholarly import scholarly as _scholarly
        _scholarly_available = True
    except ImportError:
        print("INFO: 'scholarly' not installed — Google Scholar fallback disabled.")
        print("      Install with: pip install scholarly")


def fetch_google_scholar(title):
    """Search Google Scholar via `scholarly` and return abstract, or None."""
    if not _scholarly_available:
        return None
    try:
        results = _scholarly.search_pubs(title)
        pub = next(results, None)
        if pub is None:
            return None
        filled   = _scholarly.fill(pub)
        abstract = (filled.get("bib", {}).get("abstract") or "").strip()
        if abstract:
            return re.sub(r"\s+", " ", abstract)
    except StopIteration:
        pass
    except Exception as exc:
        print(f"        [Scholar] error: {exc}")
    return None


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Loading {BIB_FILE} …", flush=True)
    with open(BIB_FILE, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    entries = db.entries
    print(f"  {len(entries)} entries found.\n", flush=True)

    found_keys   = []
    missing_keys = []
    skipped_keys = []
    source_counts = {
        "arxiv_html": 0, "semantic_scholar": 0,
        "openalex": 0,   "google_scholar": 0,
    }

    for i, entry in enumerate(entries, 1):
        key      = entry.get("ID", f"entry_{i}")
        title    = clean_latex(entry.get("title", ""))
        author   = entry.get("author", "")
        eprint   = entry.get("eprint", "").strip()
        out_path = ABSTRACT_DIR / f"{slug(key)}.txt"

        print(f"[{i:3d}/{len(entries)}] {key}", flush=True)

        if SKIP_EXISTING and out_path.exists():
            print("        → exists, skipping.", flush=True)
            skipped_keys.append(key)
            continue

        if not title:
            print("        → no title, skipping.", flush=True)
            missing_keys.append((key, "no title in BibTeX"))
            continue

        abstract = None
        source   = None

        # 1. arXiv HTML scrape
        if eprint:
            print(f"        [1] arXiv HTML ({eprint}) …", end=" ", flush=True)
            abstract = fetch_arxiv_html(eprint)
            if abstract:
                source = "arxiv_html"
                print(f"✓ {len(abstract)} chars", flush=True)
            else:
                print("✗", flush=True)
            time.sleep(DELAY_ARXIV)

        # 2. Semantic Scholar
        if not abstract and USE_SEMANTIC_S2:
            print(f"        [2] Semantic Scholar …", end=" ", flush=True)
            abstract = fetch_semantic_scholar(title, first_author_last(author))
            if abstract:
                source = "semantic_scholar"
                print(f"✓ {len(abstract)} chars", flush=True)
            else:
                print("✗", flush=True)
            time.sleep(DELAY_S2)

        # 3. OpenAlex
        if not abstract and USE_OPENALEX:
            print(f"        [3] OpenAlex …", end=" ", flush=True)
            abstract = fetch_openalex(title)
            if abstract:
                source = "openalex"
                print(f"✓ {len(abstract)} chars", flush=True)
            else:
                print("✗", flush=True)
            time.sleep(DELAY_OPENALEX)

        # 4. Google Scholar
        if not abstract and USE_SCHOLARLY:
            print(f"        [4] Google Scholar …", end=" ", flush=True)
            abstract = fetch_google_scholar(title)
            if abstract:
                source = "google_scholar"
                print(f"✓ {len(abstract)} chars", flush=True)
            else:
                print("✗", flush=True)
            time.sleep(DELAY_SCHOLAR)

        if abstract:
            out_path.write_text(abstract, encoding="utf-8")
            source_counts[source] += 1
            found_keys.append((key, source))
        else:
            missing_keys.append((key, "not found in any source"))
            print(f"        ✗ not found in any source", flush=True)

    # ── summary ───────────────────────────────────────────────────────────────
    n_found = len(found_keys)
    n_skip  = len(skipped_keys)
    n_miss  = len(missing_keys)

    lines = [
        "Abstract Fetch Summary",
        "=" * 60,
        f"BibTeX entries       : {len(entries)}",
        f"Already existed      : {n_skip}",
        f"Newly fetched        : {n_found}",
        f"  via arXiv HTML     : {source_counts['arxiv_html']}",
        f"  via Semantic Scholar: {source_counts['semantic_scholar']}",
        f"  via OpenAlex       : {source_counts['openalex']}",
        f"  via Google Scholar : {source_counts['google_scholar']}",
        f"Not found            : {n_miss}",
        "",
    ]
    if found_keys:
        lines += ["FETCHED", "-" * 60]
        lines += [f"  {k:45s} [{s}]" for k, s in found_keys]
        lines.append("")
    if missing_keys:
        lines += ["MISSING / NOT FOUND", "-" * 60]
        lines += [f"  {k:45s} ({r})" for k, r in missing_keys]
        lines.append("")
    if skipped_keys:
        lines += ["SKIPPED (already existed)", "-" * 60]
        lines += [f"  {k}" for k in skipped_keys]
        lines.append("")

    summary_text = "\n".join(lines)
    SUMMARY_FILE.write_text(summary_text, encoding="utf-8")
    print("\n" + summary_text, flush=True)
    print(f"Summary written to {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
