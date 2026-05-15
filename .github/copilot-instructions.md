# Copilot Instructions

## Build / Run

Regenerate all HTML from `cs.bib`:

```bash
cd /path/to/www2
python3 generate.py
```

**Dependency:** `bibtexparser`. Use `uv` (not pip/conda) to install:
```bash
uv pip install bibtexparser
```

**Output:**
- `index.html` — publication list page (all papers)
- `details/<key>.html` — one detail page per BibTeX entry

## Architecture

This is a **static site generator** — a single Python script (`generate.py`) reads `cs.bib` and writes all HTML. There is no framework, no server, and no build system beyond running the script directly.

```
cs.bib              ← source of truth for all publications
generate.py         ← parses cs.bib → writes index.html + details/*.html
abstract/<key>.txt  ← optional per-paper abstract text files
details/*.html      ← generated detail pages (one per BibTeX key)
index.html          ← generated publication list page
html_examples/      ← reference screenshots (a1.jpg, a2.jpg, a3.jpg)
```

**Data flow inside `generate.py`:**
1. Parse `cs.bib` with `bibtexparser`
2. For each entry: call `make_detail(e)` → write `details/<slug(key)>.html`
3. Call `build_index(entries)` → write `index.html`
4. All HTML is emitted as Python f-strings — no template engine

**Client-side interactivity** on `index.html` is driven by an inline JSON data blob (`js_data`) embedded at page bottom; JavaScript reads it to power real-time search, venue filtering, year navigation, and abstract preview popups.

## Key Conventions

### Self-contained HTML — no external assets except MathJax
All CSS lives in `<style>` blocks inside each HTML file (`SHARED_CSS` constant + page-specific additions). No external CSS files, no frameworks. MathJax 3 is the only CDN dependency, loaded from jsDelivr for `$...$` inline math rendering.

### BibTeX key → filename mapping
`slug(key)` converts a BibTeX key to a filename by replacing non-alphanumeric characters with `_`. The detail file is `details/<slug>.html` and links from `index.html` use `details/<slug>.html`.

### LaTeX in titles/abstracts
- `clean_latex()` strips LaTeX markup while **preserving `$...$` math spans** for MathJax
- `$...$` math in titles is rendered client-side by MathJax (not pre-converted)
- Author names use "Last, First" → "First Last" normalisation in `fmt_authors()`

### Chunhua Shen highlighting
Wherever author lists are rendered, "Chunhua Shen" is wrapped in `<span style="text-decoration:underline">` (detail pages) or `<span class="cs-author">` (index page).

### Abstract source
Abstracts are read from `abstract/<key>.txt` files (one plain-text file per entry). If no `.txt` file exists, the abstract field from `cs.bib` is used as a fallback.

### BibTeX block format (Rule 3)
`make_bibtex_block(e)` always outputs only: `title`, `author`, `booktitle`/`journal`, `year`, and `note` (if present) — fields are column-aligned with padding to the longest field name.

### Page header format (Rule 1)
The index page header must follow:
```html
<div class="page-header"><h1>Publications</h1><p>N publications by Chunhua Shen</p></div>
```

### Venue field
Papers use a custom `venue` field in the BibTeX for short venue names (e.g., `CVPR`, `TPAMI`). `venue_of(e)` reads this. `pub_venue_str(e)` builds the full human-readable string from `booktitle`/`journal` + year.

### Adding a new publication
1. Add a new entry to `cs.bib`
2. Optionally create `abstract/<key>.txt` with the abstract text
3. Run `python3 generate.py` — all HTML is regenerated automatically
