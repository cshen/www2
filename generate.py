#!/usr/bin/env python3
"""
generate.py — Static site generator for Chunhua Shen's publications.

Reads cs.bib → writes index.html and details/<key>.html for each entry.

Usage:
    python3 generate.py

Dependencies:
    uv pip install bibtexparser
"""

import os
import re
import json
import html as html_lib
import bibtexparser
from bibtexparser.bparser import BibTexParser
from config import (
    BIB_FILE, ABSTRACT_DIR, DETAILS_DIR,
    AUTHOR_NAME, PRIMARY_VENUES, VENUE_ORDER,
    SITE_BASE_URL, GITHUB_REPO_URL,
)

MATHJAX_CDN = (
    '<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" '
    'id="MathJax-script" async></script>'
)

MATHJAX_CONFIG = """
<script>
MathJax = {
  tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] },
  options: { skipHtmlTags: ['script','noscript','style','textarea','pre'] }
};
</script>
"""

# Editorial fonts: Cormorant Garamond (high-contrast display serif) +
# Barlow Condensed (compact magazine-label sans)
GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:'
    'ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,600'
    '&family=Barlow+Condensed:wght@300;400;500;600;700'
    '&display=swap" rel="stylesheet">'
)

THEME_TOGGLE_BTN = """\
<button class="theme-toggle" id="theme-toggle" aria-label="Toggle light/dark theme" title="Toggle light/dark theme">
    <svg class="icon-moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/></svg>
    <svg class="icon-sun"  viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
  </button>"""

THEME_TOGGLE_JS = """\
(function() {
  var saved = localStorage.getItem('theme');
  if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
})();
"""

THEME_TOGGLE_JS_HANDLER = """\
document.getElementById('theme-toggle').addEventListener('click', function() {
  var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
});
"""

# ---------------------------------------------------------------------------
# Shared CSS  — Editorial / Magazine aesthetic (Rules 23 & 24)
# Inspired by Esquire, Vogue, GQ: oversized serif display type,
# clean ink-on-newsprint palette, condensed sans for all UI labels.
# ---------------------------------------------------------------------------

SHARED_CSS = """
:root {
  --bg:           #F9F7F3;
  --bg-card:      #FFFFFF;
  --ink:          #0D0D0D;
  --ink-mid:      #38352F;
  --ink-light:    #7A756D;
  --rule:         #DDD9D0;
  --rule-strong:  #C4BFB5;
  --accent:       #9E1515;
  --accent-hover: #BF2020;
  --accent-pale:  rgba(158,21,21,0.07);
  --disp:         'Cormorant Garamond', 'Palatino Linotype', Georgia, serif;
  --ui:           'Barlow Condensed', 'Arial Narrow', Helvetica, sans-serif;
}

[data-theme="dark"] {
  --bg:           #141210;
  --bg-card:      #1C1A17;
  --ink:          #EDE9E1;
  --ink-mid:      #C4BFAF;
  --ink-light:    #A89F94;
  --rule:         #2E2B26;
  --rule-strong:  #3D3830;
  --accent:       #D94840;
  --accent-hover: #E85E55;
  --accent-pale:  rgba(217,72,64,0.14);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }

body {
  font-family: var(--disp);
  font-size: 18px;
  line-height: 1.65;
  color: var(--ink);
  background: var(--bg);
  min-height: 100vh;
}

a { color: inherit; text-decoration: none; }
a:hover { color: var(--accent); }

/* Thin accent stripe at very top — classic magazine detail */
body::before {
  content: '';
  display: block;
  height: 3px;
  background: var(--ink);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 200;
}

.page-wrap { max-width: 1200px; margin: 0 auto; }
.container  { max-width: 1100px; margin: 0 auto; padding: 0 48px; }

/* ════════════════════════════════════════
   SITE HEADER
   ════════════════════════════════════════ */
.site-header {
  position: sticky;
  top: 3px;           /* below the accent stripe */
  z-index: 100;
  background: var(--bg);
  border-bottom: 1px solid var(--ink);
}
.site-header .inner {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 14px 48px;
  max-width: 1100px;
  margin: 0 auto;
}
.site-logo {
  font-family: var(--disp);
  font-size: 17px;
  font-weight: 500;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink);
  white-space: nowrap;
}
.site-logo:hover { color: var(--accent); }

/* ── Theme toggle ── */
.theme-toggle {
  margin-left: 16px;
  flex-shrink: 0;
  background: transparent;
  border: 1px solid var(--rule-strong);
  border-radius: 100px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--ink-mid);
  transition: border-color .14s, color .14s, background .14s;
}
.theme-toggle:hover { border-color: var(--ink); color: var(--ink); background: var(--rule); }
.theme-toggle svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
/* show correct icon per theme */
.icon-moon { display: block; }
.icon-sun  { display: none; }
[data-theme="dark"] .icon-moon { display: none; }
[data-theme="dark"] .icon-sun  { display: block; }

.search-wrap { flex: 1; max-width: 360px; margin-left: auto; }
.search-box {
  width: 100%;
  padding: 7px 0;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--rule-strong);
  font-family: var(--disp);
  font-size: 15px;
  font-style: italic;
  color: var(--ink);
  outline: none;
  transition: border-color .2s;
}
.search-box::placeholder { color: var(--ink-light); font-style: italic; }
.search-box:focus { border-bottom-color: var(--ink); }

/* ════════════════════════════════════════
   PAGE HEADER  (masthead)
   ════════════════════════════════════════ */
.page-header {
  padding: 64px 0 36px;
  border-bottom: 2px solid var(--ink);
}
.page-header-rule {
  height: 1px;
  background: var(--rule-strong);
  margin-bottom: 32px;
}
.page-header h1 {
  font-family: var(--disp);
  font-size: clamp(36px, 5vw, 64px);
  font-weight: 400;
  letter-spacing: 0.08em;
  line-height: 1.05;
  color: var(--ink);
  text-transform: uppercase;
}
.page-header p {
  margin-top: 18px;
  font-family: var(--disp);
  font-size: 18px;
  font-weight: 400;
  font-style: italic;
  letter-spacing: 0.06em;
  color: var(--ink-light);
}

/* ════════════════════════════════════════
   VENUE FILTERS  (Rule 11)
   ════════════════════════════════════════ */
.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 16px 0 20px;
  border-bottom: 1px solid var(--rule);
}
.filter-btn {
  padding: 4px 13px;
  border: 1px solid var(--rule-strong);
  border-radius: 100px;
  background: transparent;
  font-family: var(--ui);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-mid);
  cursor: pointer;
  transition: all .14s;
  position: relative;
}
.filter-btn:hover { border-color: var(--ink); color: var(--ink); }
.filter-btn.active {
  background: var(--ink);
  color: var(--bg);
  border-color: var(--ink);
}
.filter-btn.secondary-venue         { display: none; }
.filter-btn.secondary-venue.revealed { display: inline-flex; }

/* ── Custom tooltip ── */
.filter-btn[data-tooltip]::before,
.filter-btn[data-tooltip]::after {
  position: absolute;
  bottom: calc(100% + 14px);
  left: 50%;
  transform: translateX(-50%) translateY(6px);
  opacity: 0;
  pointer-events: none;
  transition: opacity .22s ease, transform .22s ease;
}
.filter-btn[data-tooltip]::after {
  content: attr(data-tooltip);
  white-space: nowrap;
  background: var(--ink);
  color: var(--bg);
  font-family: var(--disp);
  font-size: 14px;
  font-weight: 400;
  font-style: italic;
  letter-spacing: 0.04em;
  text-transform: none;
  padding: 9px 18px;
  border-radius: 8px;
  box-shadow: 0 8px 28px rgba(0,0,0,0.22), 0 2px 8px rgba(0,0,0,0.12);
  z-index: 10000;
}
.filter-btn[data-tooltip]::before {
  content: '';
  width: 0;
  height: 0;
  border-left: 7px solid transparent;
  border-right: 7px solid transparent;
  border-top: 8px solid var(--ink);
  bottom: calc(100% + 6px);
  z-index: 10001;
}
.filter-btn[data-tooltip]:hover::before,
.filter-btn[data-tooltip]:hover::after {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
/* accent stripe on tooltip */
.filter-btn[data-tooltip]::after {
  border-top: 3px solid var(--accent);
}

.show-more-venues {
  font-family: var(--ui);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 4px;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.show-more-venues:hover { color: var(--accent-hover); }

/* ════════════════════════════════════════
   LAYOUT
   ════════════════════════════════════════ */
.layout {
  display: flex;
  gap: 0;
  align-items: flex-start;
  padding-top: 0;
}

/* Year sidebar */
.year-nav { width: 76px; flex-shrink: 0; padding-top: 48px; }
.year-nav-inner { position: sticky; top: 72px; }
.year-nav a {
  display: block;
  font-family: var(--ui);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.1em;
  padding: 4px 0;
  color: var(--ink-light);
  text-transform: uppercase;
  transition: color .14s;
}
.year-nav a:hover,
.year-nav a.active { color: var(--accent); font-weight: 700; }

/* ════════════════════════════════════════
   PUBLICATION LIST
   ════════════════════════════════════════ */
.pub-list { flex: 1; min-width: 0; }

.year-group { margin-bottom: 0; }

/* Large editorial chapter number */
.year-heading {
  font-family: var(--disp);
  font-size: clamp(28px, 3.5vw, 44px);
  font-weight: 400;
  color: var(--ink);
  letter-spacing: 0.04em;
  line-height: 1;
  padding: 40px 0 10px;
  border-bottom: 1px solid var(--rule-strong);
  margin-bottom: 0;
}

.pub-entry {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px 0;
  border-bottom: 1px solid var(--rule);
  position: relative;
  animation: entryFadeIn 0.44s ease both;
}
.pub-entry:hover {
  background: var(--bg-card);
}

@keyframes entryFadeIn {
  from { opacity: 0; transform: translateY(7px); }
  to   { opacity: 1; transform: translateY(0); }
}

.pub-main { flex: 1; min-width: 0; }

.pub-title {
  font-family: var(--disp);
  font-size: 19.5px;
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 7px;
  color: var(--ink);
}
.pub-title a { color: var(--ink); }
.pub-title a:hover { color: var(--accent); }

.pub-authors {
  font-family: var(--disp);
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-light);
  margin-bottom: 4px;
  line-height: 1.65;
}
.cs-author { text-decoration: underline; color: var(--ink-mid); }

.pub-venue {
  font-family: var(--disp);
  font-size: 15px;
  font-style: italic;
  color: var(--ink-light);
}

.pub-note {
  display: inline-block;
  margin-top: 8px;
  font-family: var(--disp);
  font-size: 13px;
  font-style: italic;
  font-weight: 400;
  letter-spacing: 0.02em;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 2px 12px;
  border-radius: 4px;
}

/* ── Preview button & popup ── */
/* z-index escalation handled in JS when popup opens */
.pub-preview-wrap { position: relative; flex-shrink: 0; }
.pub-entry { isolation: auto; }
.pub-entry.popup-open { isolation: isolate; z-index: 9999; position: relative; }

.btn-preview {
  display: inline-flex;
  align-items: center;
  padding: 9px 22px;
  background: transparent;
  color: var(--ink-mid);
  border: 1px solid var(--rule-strong);
  border-radius: 100px;
  font-family: var(--disp);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
  white-space: nowrap;
  transition: background .14s, color .14s, border-color .14s;
}
.btn-preview:hover { background: var(--ink); color: var(--bg); border-color: var(--ink); }

.preview-popup {
  display: none;
  position: absolute;
  right: 0;
  top: calc(100% + 12px);
  width: 440px;
  background: var(--bg-card);
  opacity: 1;
  border-top: 3px solid var(--accent);
  box-shadow: 0 16px 60px rgba(13,13,13,0.22), 0 2px 8px rgba(13,13,13,0.10);
  padding: 28px 32px 28px;
  z-index: 9999;
  animation: popupReveal .15s ease;
}
.preview-popup.visible { display: block; }

@keyframes popupReveal {
  from { opacity: 0; transform: translateY(-7px); }
  to   { opacity: 1; transform: translateY(0); }
}

.preview-abstract {
  font-family: var(--disp);
  font-size: 16.5px;
  line-height: 1.72;
  color: var(--ink-mid);
  max-height: 280px;
  overflow-y: auto;
  margin-bottom: 22px;
  padding-right: 4px;
}
.preview-abstract::-webkit-scrollbar { width: 3px; }
.preview-abstract::-webkit-scrollbar-thumb { background: var(--rule-strong); }

.btn-view-details {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 22px;
  background: transparent;
  color: var(--ink-mid);
  border: 1px solid var(--rule-strong);
  border-radius: 100px;
  font-family: var(--disp);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
  text-decoration: none;
  transition: background .14s, color .14s, border-color .14s;
}
.btn-view-details:hover { background: var(--ink); color: var(--bg); border-color: var(--ink); }

#no-results {
  display: none;
  padding: 64px 0;
  text-align: center;
  color: var(--ink-light);
  font-style: italic;
  font-size: 19px;
}

/* ════════════════════════════════════════
   DETAIL PAGE
   ════════════════════════════════════════ */
.breadcrumb {
  font-family: var(--ui);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-light);
  padding: 36px 0 28px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.breadcrumb a { color: var(--ink-light); text-decoration: underline; text-underline-offset: 3px; }
.breadcrumb a:hover { color: var(--accent); }
.breadcrumb-sep { color: var(--rule-strong); }

.detail-title {
  font-family: var(--disp);
  font-size: clamp(30px, 4.5vw, 58px);
  font-weight: 300;
  line-height: 1.12;
  letter-spacing: 0.01em;
  color: var(--ink);
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 2px solid var(--ink);
}

.detail-meta {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 36px;
}
.detail-authors {
  font-family: var(--ui);
  font-size: 13px;
  font-weight: 400;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--ink-light);
  line-height: 1.7;
}
.cs-author-detail { text-decoration: underline; color: var(--ink-mid); }

.detail-venue {
  font-family: var(--disp);
  font-size: 17px;
  font-style: italic;
  color: var(--ink-light);
}

.detail-note {
  display: inline-block;
  margin-top: 10px;
  font-family: var(--ui);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 3px 10px;
  border-radius: 2px;
}

/* ── Action buttons ── */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 60px;
  padding-bottom: 44px;
  border-bottom: 1px solid var(--rule);
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--rule-strong);
  border-radius: 100px;
  font-family: var(--ui);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
  text-decoration: none;
  transition: all .14s;
  line-height: 1;
}
.action-btn:hover {
  background: var(--ink);
  color: var(--bg);
  border-color: var(--ink);
  text-decoration: none;
}
.action-btn svg { width: 13px; height: 13px; fill: currentColor; flex-shrink: 0; }

/* ── Abstract / BibTeX sections ── */
.section { margin-bottom: 64px; }

.section-grid {
  display: grid;
  grid-template-columns: 148px 1fr;
  gap: 44px;
  align-items: start;
}
.section-label {
  font-family: var(--ui);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-light);
  padding-top: 6px;
  border-top: 1px solid var(--rule-strong);
}
.section-content {
  font-family: var(--disp);
  font-size: 18px;
  line-height: 1.76;
  color: var(--ink-mid);
}

/* BibTeX code block */
.bibtex-block {
  background: var(--bg-card);
  border: 1px solid var(--rule);
  border-left: 3px solid var(--ink);
  padding: 20px 26px;
  font-family: 'Courier New', 'Lucida Console', monospace;
  font-size: 12.5px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
  color: var(--ink-mid);
}

/* ── Footer ── */
.site-footer {
  border-top: 2px solid var(--ink);
  padding: 28px 0;
  margin-top: 96px;
}
.site-footer p {
  font-family: var(--ui);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-light);
  text-align: center;
}
.site-footer a { color: var(--ink-light); text-decoration: underline; }
.site-footer a:hover { color: var(--accent); }

/* ── Responsive ── */
@media (max-width: 768px) {
  .container  { padding: 0 20px; }
  .site-header .inner { padding: 14px 20px; }
  .layout { flex-direction: column; }
  .year-nav { width: 100%; padding-top: 20px; }
  .year-nav-inner { position: static; display: flex; flex-wrap: wrap; gap: 4px 16px; }
  .section-grid { grid-template-columns: 1fr; gap: 12px; }
  .preview-popup { width: 310px; right: auto; left: 0; }
  .page-header h1 { font-size: 32px; }
  .detail-title { font-size: 30px; }
}
"""

# ---------------------------------------------------------------------------
# Utility functions  (unchanged)
# ---------------------------------------------------------------------------

def slug(key: str) -> str:
    """BibTeX key → safe filename (non-alphanumeric → underscore)."""
    return re.sub(r'[^A-Za-z0-9]', '_', key)


def clean_latex(text: str) -> str:
    """Strip LaTeX commands from text, preserving $...$ math spans."""
    if not text:
        return ""
    text = re.sub(r'\{([^{}]*)\}', r'\1', text)
    text = re.sub(r'\{([^{}]*)\}', r'\1', text)
    text = text.replace('{', '').replace('}', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_latex_html(text: str) -> str:
    """Like clean_latex but HTML-escapes outside $...$ math spans."""
    if not text:
        return ""
    parts = re.split(r'(\$[^$]*\$)', text)
    result = []
    for part in parts:
        if part.startswith('$') and part.endswith('$') and len(part) > 1:
            result.append(part)  # keep math as-is for MathJax
        else:
            p = re.sub(r'\{([^{}]*)\}', r'\1', part)
            p = re.sub(r'\{([^{}]*)\}', r'\1', p)
            p = p.replace('{', '').replace('}', '')
            p = html_lib.escape(p)
            result.append(p)
    return ''.join(result)


# Words that stay lowercase in titles unless first, last, or ≥4 letters.
_MINOR = frozenset({
    # articles
    'a', 'an', 'the',
    # coordinating conjunctions (all < 4 letters)
    'and', 'but', 'or', 'nor', 'for', 'so', 'yet',
    # short prepositions (< 4 letters)
    'at', 'by', 'in', 'of', 'on', 'to', 'up', 'as', 'vs', 'per',
})


def apply_title_case(text: str) -> str:
    """Apply APA/Chicago-style title case, preserving {braces} and $math$ spans.

    Rules implemented:
    • Capitalize the first word and (after : — –) the first word of any subtitle.
    • Capitalize all words of 4+ letters.
    • Capitalize major words (anything not in _MINOR).
    • Hyphenated words: each element is evaluated independently
      (e.g. Self-Report, not Self-report).
    • Content inside {braces} or $math$ is emitted verbatim (no case change).
    """
    if not text:
        return text

    # Tokenise: protected spans first, then word-runs and non-word runs.
    tok_re = re.compile(r'(\{[^{}]*\}|\$[^$]*\$|\w+|[^\w]+)')
    tokens = tok_re.findall(text)

    result = []
    cap_next = True   # first word of title / subtitle always capitalised

    for tok in tokens:
        # ── protected: BibTeX braces or LaTeX math — emit as-is ──────────
        is_braced = tok.startswith('{') and tok.endswith('}') and len(tok) > 1
        is_math   = tok.startswith('$') and tok.endswith('$') and len(tok) > 1
        if is_braced or is_math:
            result.append(tok)
            continue

        # ── word token ────────────────────────────────────────────────────
        if re.match(r'^\w+$', tok):
            alpha = re.sub(r'[^a-zA-Z]', '', tok)   # letters only (for length)
            should_cap = (
                cap_next
                or len(alpha) >= 4
                or tok.lower() not in _MINOR
            )
            if should_cap:
                result.append(tok[0].upper() + tok[1:])  # preserve rest (acronyms)
            else:
                result.append(tok.lower())
            cap_next = False
            continue

        # ── non-word token (spaces, punctuation, hyphens) ─────────────────
        result.append(tok)
        # Colon or dash signals a subtitle → next word capitalised
        if re.search(r'[:—–]', tok):
            cap_next = True

    return ''.join(result)


def fmt_authors(author_str: str, for_detail: bool = False) -> str:
    """Parse author string → HTML with Chunhua Shen underlined, '·' separated."""
    if not author_str:
        return ""
    names_raw = re.split(r'\s+and\s+', author_str, flags=re.IGNORECASE)
    names = []
    for raw in names_raw:
        raw = re.sub(r'\s+', ' ', raw).strip()
        raw = re.sub(r'[{}]', '', raw)
        if ',' in raw:
            parts = raw.split(',', 1)
            raw = parts[1].strip() + ' ' + parts[0].strip()
        names.append(raw.strip())

    css_class = "cs-author-detail" if for_detail else "cs-author"
    html_names = []
    for n in names:
        if n == AUTHOR_NAME:
            html_names.append(f'<span class="{css_class}">{html_lib.escape(n)}</span>')
        else:
            html_names.append(html_lib.escape(n))
    return ' · '.join(html_names)


def venue_of(e: dict) -> str:
    return (e.get('venue') or '').strip()


def pub_venue_str(e: dict) -> str:
    year = (e.get('year') or '').strip()
    venue_long = (e.get('booktitle') or e.get('journal') or '').strip()
    venue_long = clean_latex(venue_long)
    if venue_long and year:
        return f"{venue_long} ({year})"
    elif venue_long:
        return venue_long
    elif year:
        return year
    return ""


def get_abstract(key: str, e: dict) -> str:
    txt_path = os.path.join(ABSTRACT_DIR, f"{key}.txt")
    if os.path.isfile(txt_path):
        with open(txt_path, encoding='utf-8', errors='replace') as f:
            return f.read().strip()
    fallback = (e.get('abstract') or '').strip()
    if fallback:
        return clean_latex(fallback)
    return ""


def note_clean(note: str) -> str:
    """Strip trailing punctuation from note text."""
    if not note:
        return ""
    return note.strip().rstrip('.,;:!?')


def venue_sort_key(v: str) -> int:
    """Return sort key for venue (lower = higher prestige). Exact match only."""
    v_upper = v.strip().upper()
    for i, pv in enumerate(VENUE_ORDER):
        if pv.upper() == v_upper:
            return i
    return len(VENUE_ORDER)


def make_bibtex_block(e: dict) -> str:
    """Clean BibTeX block: title, author, booktitle/journal, year, note (if any)."""
    entry_type = e.get('ENTRYTYPE', 'misc').lower()
    key = e.get('ID', '')

    fields = []
    fields.append(('title',  (e.get('title') or '').strip()))
    fields.append(('author', (e.get('author') or '').strip()))
    if e.get('booktitle'):
        fields.append(('booktitle', e['booktitle'].strip()))
    elif e.get('journal'):
        fields.append(('journal', e['journal'].strip()))
    fields.append(('year', (e.get('year') or '').strip()))
    note = note_clean(e.get('note') or '')
    if note:
        fields.append(('note', note))

    max_len = max(len(f[0]) for f in fields)
    lines = [f"@{entry_type}{{{key},"]
    for fname, fval in fields:
        padding = ' ' * (max_len - len(fname))
        lines.append(f"  {fname}{padding} = {{{fval}}},")
    lines.append("}")
    return '\n'.join(lines)


def parse_bib() -> list:
    """Parse cs.bib and return list of entry dicts, sorted newest-first."""
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    with open(BIB_FILE, encoding='utf-8', errors='replace') as f:
        bdb = bibtexparser.load(f, parser=parser)

    entries = []
    for e in bdb.entries:
        for k in list(e.keys()):
            if isinstance(e[k], str) and e[k].strip() == '{}':
                e[k] = ''
        entries.append(e)

    def sort_key(e):
        year_str = (e.get('year') or '0').strip()
        try:
            year = int(year_str)
        except ValueError:
            year = 0
        return (-year, venue_sort_key(venue_of(e)))

    entries.sort(key=sort_key)
    return entries


# ---------------------------------------------------------------------------
# Detail page generator
# ---------------------------------------------------------------------------

def make_detail(e: dict) -> str:
    """Generate the full HTML for a detail page."""
    key = e.get('ID', '')
    title_raw = apply_title_case((e.get('title') or 'Untitled').strip())
    title_html = clean_latex_html(title_raw)
    title_plain = clean_latex(title_raw)
    title_plain_short = title_plain[:60] + ('…' if len(title_plain) > 60 else '')

    authors_html = fmt_authors(e.get('author') or '', for_detail=True)
    venue_str = pub_venue_str(e)
    note = note_clean(e.get('note') or '')
    abstract = get_abstract(key, e)
    bibtex = make_bibtex_block(e)
    bibtex_escaped = html_lib.escape(bibtex)

    # ── Action buttons (conditional on field presence) ──
    btns = []

    pdf = (e.get('pdf') or '').strip()
    if pdf:
        btns.append(f'<a href="{html_lib.escape(pdf)}" class="action-btn" target="_blank" rel="noopener">'
                    '<svg viewBox="0 0 24 24"><path d="M5 20h14v-2H5v2zm7-18L5.33 9h3.84v4h5.66V9h3.84L12 2z"/></svg>'
                    'Download</a>')

    eprint = (e.get('eprint') or '').strip()
    if eprint:
        arxiv_url = f"https://arxiv.org/abs/{eprint}"
        btns.append(f'<a href="{arxiv_url}" class="action-btn" target="_blank" rel="noopener">'
                    '<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>'
                    'arXiv</a>')

    project = (e.get('project') or '').strip()
    if project:
        btns.append(f'<a href="{html_lib.escape(project)}" class="action-btn" target="_blank" rel="noopener">'
                    '<svg viewBox="0 0 24 24"><path d="M11 7H6a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>'
                    'Project Page</a>')

    title_for_scholar = clean_latex(title_raw)
    gs_url = f"https://scholar.google.com/scholar?q={html_lib.escape(title_for_scholar.replace(' ', '+'))}"
    btns.append(f'<a href="{gs_url}" class="action-btn" target="_blank" rel="noopener">'
                '<svg viewBox="0 0 24 24"><path d="M12 3L1 9l4 2.18V17l7 4 7-4v-5.82L23 9 12 3zm6 12.82L12 19l-6-3.18V12.5l6 3.5 6-3.5v3.32z"/></svg>'
                'Google Scholar</a>')

    # Share buttons (only if SITE_BASE_URL is configured)
    detail_url = f"details/{slug(key)}.html"
    if SITE_BASE_URL:
        base = SITE_BASE_URL.rstrip('/')
        share_twitter  = f"https://twitter.com/intent/tweet?text={html_lib.escape(title_plain)}&url={base}/{detail_url}"
        share_linkedin = f"https://www.linkedin.com/sharing/share-offsite/?url={base}/{detail_url}"
        btns.append(f'<a href="{share_twitter}" class="action-btn" target="_blank" rel="noopener" title="Share on X / Twitter">'
                    '<svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.737-8.835L1.254 2.25H8.08l4.259 5.63 5.905-5.63zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'
                    '</a>')
        btns.append(f'<a href="{share_linkedin}" class="action-btn" target="_blank" rel="noopener" title="Share on LinkedIn">'
                    '<svg viewBox="0 0 24 24"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/></svg>'
                    '</a>')

    # Report issue button (only if GITHUB_REPO_URL is configured)
    if GITHUB_REPO_URL:
        report_title = html_lib.escape(f"Issue: {title_plain[:60]}")
        report_body  = html_lib.escape(f"BibTeX key: {key}\n\nIssue description:\n")
        report_url   = f"{GITHUB_REPO_URL.rstrip('/')}/issues/new?title={report_title}&body={report_body}"
        btns.append(f'<a href="{report_url}" class="action-btn" target="_blank" rel="noopener" title="Report an issue">'
                    '<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>'
                    '</a>')

    note_html = ''
    if note:
        note_html = f'<div class="detail-note">{html_lib.escape(note)}</div>'

    abstract_content = html_lib.escape(abstract) if abstract else '<em>Abstract not available.</em>'
    btns_html = '\n    '.join(btns)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_lib.escape(title_plain_short)} — {AUTHOR_NAME}</title>
  <meta name="description" content="{html_lib.escape(abstract[:160] if abstract else title_plain)}">
  {GOOGLE_FONTS}
  {MATHJAX_CONFIG}
  {MATHJAX_CDN}
  <style>
{SHARED_CSS}
  </style>
  <script>{THEME_TOGGLE_JS}</script>
</head>
<body>
<div class="page-wrap">

<header class="site-header">
  <div class="inner">
    <a href="../index.html" class="site-logo">{AUTHOR_NAME}</a>
    {THEME_TOGGLE_BTN}
  </div>
</header>

<main class="container">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="../index.html">Home</a>
    <span class="breadcrumb-sep">›</span>
    <a href="../index.html">Publications</a>
    <span class="breadcrumb-sep">›</span>
    <span aria-current="page">{html_lib.escape(title_plain_short)}</span>
  </nav>

  <h1 class="detail-title">{title_html}</h1>

  <div class="detail-meta">
    <div class="detail-authors">{authors_html}</div>
    <div class="detail-venue">{html_lib.escape(venue_str)}</div>
    {note_html}
  </div>

  <div class="action-buttons" role="group" aria-label="Publication actions">
    <button class="action-btn" id="copy-bibtex-btn" onclick="copyBibtex(this)" title="Copy BibTeX to clipboard">
      <svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
      Copy BibTeX</button>
    {btns_html}
  </div>

  <section class="section" aria-labelledby="abstract-lbl">
    <div class="section-grid">
      <h2 class="section-label" id="abstract-lbl">Abstract</h2>
      <div class="section-content">{abstract_content}</div>
    </div>
  </section>

  <section class="section" aria-labelledby="bibtex-lbl">
    <div class="section-grid">
      <h2 class="section-label" id="bibtex-lbl">BibTeX</h2>
      <div>
        <div class="bibtex-block" id="bibtex-content" role="region" aria-label="BibTeX citation">{bibtex_escaped}</div>
      </div>
    </div>
  </section>
</main>

</div><!-- .page-wrap -->

<footer class="site-footer">
  <p>© {AUTHOR_NAME} &nbsp;·&nbsp; <a href="../index.html">Publications</a></p>
</footer>

<script>
function copyBibtex(btn) {{
  var text = document.getElementById('bibtex-content').textContent;
  navigator.clipboard.writeText(text).then(function() {{
    var orig = btn.innerHTML;
    btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> Copied!';
    setTimeout(function() {{ btn.innerHTML = orig; }}, 2000);
  }});
}}
{THEME_TOGGLE_JS_HANDLER}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Index page generator
# ---------------------------------------------------------------------------

def build_index(entries: list) -> str:
    """Build index.html with all publications."""
    total = len(entries)

    from collections import OrderedDict
    years_dict: dict = OrderedDict()
    for e in entries:
        year = (e.get('year') or 'Unknown').strip()
        years_dict.setdefault(year, []).append(e)

    # Rule 11: fixed primary + secondary venue buttons
    venue_counts: dict = {}
    for e in entries:
        v = venue_of(e)
        if v:
            venue_counts[v] = venue_counts.get(v, 0) + 1

    secondary_venues = [v for v, c in sorted(venue_counts.items(),
                        key=lambda x: (-x[1], x[0]))
                        if v not in PRIMARY_VENUES and c >= 2]
    secondary_venues.sort(key=lambda v: (venue_sort_key(v), v))

    filter_btns = '<button class="filter-btn active" data-venue="all">All</button>\n'
    for v in PRIMARY_VENUES:
        if v in venue_counts:
            n = venue_counts[v]
            tip = f"Show {n} {html_lib.escape(v)} paper{'s' if n != 1 else ''} authored by {AUTHOR_NAME}"
            filter_btns += f'    <button class="filter-btn" data-venue="{html_lib.escape(v)}" data-tooltip="{tip}">{html_lib.escape(v)}</button>\n'
    for v in secondary_venues:
        filter_btns += f'    <button class="filter-btn secondary-venue" data-venue="{html_lib.escape(v)}">{html_lib.escape(v)}</button>\n'
    if secondary_venues:
        filter_btns += '    <button class="show-more-venues" id="show-more-btn" onclick="toggleMoreVenues()">Show all venues</button>\n'

    year_nav_links = '\n'.join(
        f'    <a href="#{y}" data-year="{y}">{y}</a>'
        for y in years_dict
    )

    pub_html_parts = []
    js_data = []

    for year, year_entries in years_dict.items():
        year_html  = f'  <div class="year-group" id="{year}" data-year="{year}">\n'
        year_html += f'    <h2 class="year-heading">{html_lib.escape(year)}</h2>\n'

        for i, e in enumerate(year_entries):
            key        = e.get('ID', '')
            sl         = slug(key)
            title_raw  = apply_title_case((e.get('title') or 'Untitled').strip())
            title_html = clean_latex_html(title_raw)
            title_plain = clean_latex(title_raw)
            authors_html = fmt_authors(e.get('author') or '')
            venue_str  = pub_venue_str(e)
            venue_short = venue_of(e)
            note       = note_clean(e.get('note') or '')
            abstract   = get_abstract(key, e)

            note_html = ''
            if note:
                note_html = f'<span class="pub-note">{html_lib.escape(note)}</span>'

            abstract_preview = abstract if abstract else 'Abstract not available.'
            detail_url = f"details/{sl}.html"

            js_data.append({
                'key':     key,
                'title':   title_plain.lower(),
                'authors': clean_latex(e.get('author') or '').lower(),
                'venue':   venue_short,
                'year':    year,
            })

            anim_delay = f"animation-delay:{min(i * 0.04, 0.6):.2f}s"

            year_html += f'''    <div class="pub-entry" data-key="{key}" data-venue="{html_lib.escape(venue_short)}" data-year="{year}" style="{anim_delay}">
      <div class="pub-main">
        <div class="pub-title"><a href="{detail_url}">{title_html}</a></div>
        <div class="pub-authors">{authors_html}</div>
        <div class="pub-venue">{html_lib.escape(venue_str)}</div>
        {note_html}
      </div>
      <div class="pub-preview-wrap">
        <button class="btn-preview" aria-expanded="false" aria-controls="popup-{sl}" onclick="togglePreview(this)">Preview</button>
        <div class="preview-popup" id="popup-{sl}" role="dialog" aria-label="Abstract preview">
          <div class="preview-abstract">{html_lib.escape(abstract_preview)}</div>
          <a href="{detail_url}" class="btn-view-details">View details</a>
        </div>
      </div>
    </div>\n'''

        year_html += '  </div>\n'
        pub_html_parts.append(year_html)

    pubs_html    = '\n'.join(pub_html_parts)
    js_data_json = json.dumps(js_data, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Publications — {AUTHOR_NAME}</title>
  <meta name="description" content="Publications of {AUTHOR_NAME} — {total} papers in computer vision and machine learning.">
  {GOOGLE_FONTS}
  {MATHJAX_CONFIG}
  {MATHJAX_CDN}
  <style>
{SHARED_CSS}
  </style>
  <script>{THEME_TOGGLE_JS}</script>
</head>
<body>
<div class="page-wrap">

<header class="site-header" role="banner">
  <div class="inner">
    <a href="index.html" class="site-logo">{AUTHOR_NAME}</a>
    <div class="search-wrap">
      <input type="search" class="search-box" id="search-input"
        placeholder="Search title, author, venue…"
        aria-label="Search publications"
        autocomplete="off">
    </div>
    {THEME_TOGGLE_BTN}
  </div>
</header>

<main class="container" id="main-content">
  <div class="page-header">
    <div class="page-header-rule"></div>
    <h1>Publications</h1>
    <p>{total} publications by {AUTHOR_NAME}</p>
  </div>

  <div class="filters" role="group" aria-label="Filter by venue">
    {filter_btns}
  </div>

  <div class="layout">
    <nav class="year-nav" aria-label="Jump to year">
      <div class="year-nav-inner">
{year_nav_links}
      </div>
    </nav>

    <div class="pub-list" id="pub-list" aria-live="polite">
{pubs_html}
      <div id="no-results" role="status">No publications match your search.</div>
    </div>
  </div>
</main>

</div><!-- .page-wrap -->

<footer class="site-footer" role="contentinfo">
  <p>© {AUTHOR_NAME} &nbsp;·&nbsp; {total} publications</p>
</footer>

<script>
var PUB_DATA = {js_data_json};

var venuesRevealed = false;
function toggleMoreVenues() {{
  venuesRevealed = !venuesRevealed;
  document.querySelectorAll('.filter-btn.secondary-venue').forEach(function(b) {{
    b.classList.toggle('revealed', venuesRevealed);
  }});
  var btn = document.getElementById('show-more-btn');
  if (btn) btn.textContent = venuesRevealed ? 'Show fewer venues' : 'Show all venues';
}}

// Close popups when clicking outside
document.addEventListener('click', function(e) {{
  if (!e.target.closest('.pub-preview-wrap')) {{
    document.querySelectorAll('.preview-popup.visible').forEach(function(p) {{
      p.classList.remove('visible');
      var b = p.previousElementSibling;
      if (b) b.setAttribute('aria-expanded', 'false');
      var entry = p.closest('.pub-entry');
      if (entry) entry.classList.remove('popup-open');
    }});
  }}
}});

document.addEventListener('keydown', function(e) {{
  if (e.key === 'Escape') {{
    document.querySelectorAll('.preview-popup.visible').forEach(function(p) {{
      p.classList.remove('visible');
      var b = p.previousElementSibling;
      if (b) {{ b.setAttribute('aria-expanded', 'false'); b.focus(); }}
      var entry = p.closest('.pub-entry');
      if (entry) entry.classList.remove('popup-open');
    }});
  }}
}});

function togglePreview(btn) {{
  var popup = btn.nextElementSibling;
  var isOpen = popup.classList.contains('visible');
  document.querySelectorAll('.preview-popup.visible').forEach(function(p) {{
    p.classList.remove('visible');
    var b = p.previousElementSibling;
    if (b) b.setAttribute('aria-expanded', 'false');
    var entry = p.closest('.pub-entry');
    if (entry) entry.classList.remove('popup-open');
  }});
  if (!isOpen) {{
    popup.classList.add('visible');
    btn.setAttribute('aria-expanded', 'true');
    var entry = btn.closest('.pub-entry');
    if (entry) entry.classList.add('popup-open');
  }}
}}

var activeVenue = 'all';
var searchQuery = '';

function applyFilters() {{
  var query = searchQuery.trim().toLowerCase();
  var hasResults = false;

  document.querySelectorAll('.year-group').forEach(function(yg) {{
    var yearVisible = false;
    yg.querySelectorAll('.pub-entry').forEach(function(entry) {{
      var key = entry.dataset.key;
      var venueMatch = activeVenue === 'all' || entry.dataset.venue === activeVenue;
      var textMatch = true;
      if (query) {{
        var d = PUB_DATA.find(function(p) {{ return p.key === key; }});
        if (d) {{
          textMatch = d.title.includes(query) ||
                      d.authors.includes(query) ||
                      d.venue.toLowerCase().includes(query) ||
                      d.year.includes(query);
        }}
      }}
      var show = venueMatch && textMatch;
      entry.style.display = show ? '' : 'none';
      if (show) yearVisible = true;
    }});
    yg.style.display = yearVisible ? '' : 'none';
    if (yearVisible) hasResults = true;
  }});

  document.getElementById('no-results').style.display = hasResults ? 'none' : 'block';
}}

document.getElementById('search-input').addEventListener('input', function() {{
  searchQuery = this.value;
  applyFilters();
}});

document.querySelectorAll('.filter-btn').forEach(function(btn) {{
  btn.addEventListener('click', function() {{
    document.querySelectorAll('.filter-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    btn.classList.add('active');
    activeVenue = btn.dataset.venue;
    applyFilters();
  }});
}});

// Year nav scroll highlight
var yearGroups    = document.querySelectorAll('.year-group');
var yearNavLinks  = document.querySelectorAll('.year-nav a');
function updateYearNav() {{
  var scrollY = window.scrollY + 120;
  var current = null;
  yearGroups.forEach(function(yg) {{ if (yg.offsetTop <= scrollY) current = yg.id; }});
  yearNavLinks.forEach(function(a) {{ a.classList.toggle('active', a.dataset.year === current); }});
}}
window.addEventListener('scroll', updateYearNav, {{ passive: true }});
updateYearNav();
{THEME_TOGGLE_JS_HANDLER}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(DETAILS_DIR, exist_ok=True)

    print(f"Parsing {BIB_FILE}…")
    entries = parse_bib()
    print(f"  Found {len(entries)} entries")

    print("Generating detail pages…")
    written = skipped = 0
    for i, e in enumerate(entries):
        key = e.get('ID', f'entry_{i}')
        out_path = os.path.join(DETAILS_DIR, f"{slug(key)}.html")
        if os.path.exists(out_path):
            skipped += 1
            continue
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(make_detail(e))
        written += 1

    print(f"  {written} written, {skipped} skipped (already existed)")

    print("Generating index.html…")
    index_html = build_index(entries)
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f"Done. {written + skipped} detail pages total + index.html generated.")


if __name__ == '__main__':
    main()
