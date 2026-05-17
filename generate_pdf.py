#!/usr/bin/env python3
"""
generate_pdf.py — Formal resume-style publication list PDF.

Reads cs.bib → writes publications.pdf as a simple numbered list:

   1.  Authors (Year), "Title", Venue.
   2.  Authors (Year), "Title", Venue.
   ...

Title in blue with typographic quotes.  Venue in italic.  C. Shen underlined.
Within each year: conferences first, then journals, then books.

Usage:
    python3 generate_pdf.py [output.pdf]

Dependencies:
    pip3 install reportlab
    (bibtexparser already required by generate.py)
"""

import re
import sys
from collections import OrderedDict
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, NextPageTemplate,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

from config import AUTHOR_NAME
from generate import parse_bib, apply_title_case, pub_venue_str, note_clean

# ---------------------------------------------------------------------------
# Output path
# ---------------------------------------------------------------------------

OUTPUT_PDF = sys.argv[1] if len(sys.argv) > 1 else "publications.pdf"

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

C_INK   = HexColor("#1c1c1c")   # main text
C_LIGHT = HexColor("#888888")   # secondary (footer, etc.)
C_TITLE = HexColor("#1a56db")   # paper title blue
C_NOTE  = HexColor("#1a56db")   # note text same blue
C_NUM   = HexColor("#1a56db")   # index number blue
C_HDR   = HexColor("#003087")   # masthead navy

# ---------------------------------------------------------------------------
# Font registration — Adobe Caslon Pro (Regular + Italic; no Bold)
# ---------------------------------------------------------------------------

def _reg(name, path, idx=None):
    try:
        kw = {} if idx is None else {"subfontIndex": idx}
        pdfmetrics.registerFont(TTFont(name, path, **kw))
        return True
    except Exception:
        return False

_CANDARA_R  = "/Applications/Microsoft Word.app/Contents/Resources/DFonts/Candara.ttf"
_CANDARA_I  = "/Applications/Microsoft Word.app/Contents/Resources/DFonts/Candarai.ttf"

if _reg("Candara", _CANDARA_R) and _reg("Candara-Italic", _CANDARA_I):
    registerFontFamily("Candara",
        normal="Candara", bold="Candara",
        italic="Candara-Italic", boldItalic="Candara-Italic")
    F_BODY = "Candara"
    F_ITAL = "Candara-Italic"
elif _reg("HoeflerText", "/System/Library/Fonts/Hoefler Text.ttc", 0) and \
     _reg("HoeflerText-Italic", "/System/Library/Fonts/Hoefler Text.ttc", 1):
    registerFontFamily("HoeflerText",
        normal="HoeflerText", bold="HoeflerText",
        italic="HoeflerText-Italic", boldItalic="HoeflerText-Italic")
    F_BODY = "HoeflerText"
    F_ITAL = "HoeflerText-Italic"
else:
    F_BODY = "Times-Roman"
    F_ITAL = "Times-Italic"

# ---------------------------------------------------------------------------
# Page geometry  (single-column A4)
# ---------------------------------------------------------------------------

PAGE_W, PAGE_H = A4
ML       = 22 * mm
MR       = 22 * mm
MT       = 14 * mm
MB       = 12 * mm
FOOTER_H =  8 * mm
HEADER_H = 28 * mm

BODY_W        = PAGE_W - ML - MR
FRAME_Y       = MB + FOOTER_H
FULL_FRAME_H  = PAGE_H - MT - FRAME_Y
FIRST_FRAME_H = FULL_FRAME_H - HEADER_H

# Hanging-indent width: enough room for "493." at 10.5pt
NUM_W = 28   # points

# ---------------------------------------------------------------------------
# LaTeX math → Unicode  ($...$ spans in titles)
# ---------------------------------------------------------------------------

_GREEK = {
    'alpha':'α','beta':'β','gamma':'γ','delta':'δ','epsilon':'ε',
    'zeta':'ζ','eta':'η','theta':'θ','iota':'ι','kappa':'κ',
    'lambda':'λ','mu':'μ','nu':'ν','xi':'ξ','pi':'π','rho':'ρ',
    'sigma':'σ','tau':'τ','upsilon':'υ','phi':'φ','chi':'χ',
    'psi':'ψ','omega':'ω',
    'Alpha':'Α','Beta':'Β','Gamma':'Γ','Delta':'Δ','Theta':'Θ',
    'Lambda':'Λ','Xi':'Ξ','Pi':'Π','Sigma':'Σ','Phi':'Φ',
    'Psi':'Ψ','Omega':'Ω',
}
_SUPER = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵',
          '6':'⁶','7':'⁷','8':'⁸','9':'⁹','+':'⁺','-':'⁻',
          'n':'ⁿ','i':'ⁱ','T':'ᵀ','a':'ᵃ'}
_SUB   = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅',
          '6':'₆','7':'₇','8':'₈','9':'₉','+':'₊','-':'₋',
          'n':'ₙ','i':'ᵢ','k':'ₖ'}
_SYMS  = {
    r'\infty':'∞', r'\times':'×', r'\cdot':'·', r'\ldots':'…',
    r'\dots':'…',  r'\nabla':'∇', r'\partial':'∂',
    r'\leq':'≤',   r'\geq':'≥',  r'\neq':'≠',  r'\approx':'≈',
    r'\rightarrow':'→', r'\leftarrow':'←', r'\to':'→',
    r'\in':'∈', r'\subset':'⊂', r'\cup':'∪', r'\cap':'∩',
    r'\pm':'±', r'\sqrt':'√',
}

def _math_to_unicode(s: str) -> str:
    for name, sym in _GREEK.items():
        s = re.sub(r'\\' + name + r'(?![a-zA-Z])', sym, s)
    for cmd, sym in _SYMS.items():
        s = s.replace(cmd, sym)
    def _sup(m):
        return ''.join(_SUPER.get(c, c) for c in (m.group(1) or m.group(2)))
    s = re.sub(r'\^\{([^}]*)\}|\^([^\s{\\])', _sup, s)
    def _sub(m):
        return ''.join(_SUB.get(c, c) for c in (m.group(1) or m.group(2)))
    s = re.sub(r'_\{([^}]*)\}|_([^\s{\\])', _sub, s)
    s = re.sub(r'\\[a-zA-Z]+', '', s)
    s = re.sub(r'[{}]', '', s)
    return s.strip()

def _clean_title(raw: str) -> str:
    if not raw:
        return ''
    parts = re.split(r'(\$[^$]+\$)', raw)
    out = []
    for p in parts:
        if p.startswith('$') and p.endswith('$') and len(p) > 2:
            out.append(_math_to_unicode(p[1:-1]))
        else:
            p = re.sub(r'\{([^{}]*)\}', r'\1', p)
            p = re.sub(r'\{([^{}]*)\}', r'\1', p)
            p = p.replace('{', '').replace('}', '')
            out.append(p)
    return ''.join(out).strip()

# ---------------------------------------------------------------------------
# Author abbreviation  "Firstname Last" → "F. Last"
# ---------------------------------------------------------------------------

_PARTICLES = frozenset({
    'van','de','den','der','von','di','del','le','la','los','las',
    'ter','ten','af','da','dos','du','bin','binte',
})

MAX_AUTHORS = 999

def _abbrev_one(raw: str) -> str:
    raw = re.sub(r'[{}]', '', raw).strip()
    raw = re.sub(r'\s+', ' ', raw)
    if not raw:
        return ''
    if ',' in raw:
        idx    = raw.index(',')
        last   = raw[:idx].strip()
        firsts = raw[idx+1:].strip()
        initials = ''.join(
            w[0].upper() + '.' for w in firsts.split() if w and w[0].isalpha()
        )
        return f"{initials} {last}" if initials else last
    tokens = raw.split()
    if len(tokens) == 1:
        return tokens[0]
    if len(tokens) == 2:
        return f"{tokens[0][0].upper()}. {tokens[1]}"
    last_start = len(tokens) - 1
    for i in range(1, len(tokens)):
        if tokens[i][0].islower() or tokens[i].lower() in _PARTICLES:
            last_start = i
            break
    first_tokens = tokens[:last_start]
    last_tokens  = tokens[last_start:]
    initials = ''.join(t[0].upper() + '.' for t in first_tokens if t and t[0].isalpha())
    last     = ' '.join(last_tokens)
    return f"{initials} {last}" if initials else last

def _is_primary(name: str) -> bool:
    return name.strip() == AUTHOR_NAME

def _esc(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def fmt_authors_pdf(author_str: str) -> str:
    if not author_str:
        return ''
    raw_names = re.split(r'\s+and\s+', author_str.strip(), flags=re.IGNORECASE)
    truncated = len(raw_names) > MAX_AUTHORS
    shown     = raw_names[:MAX_AUTHORS]
    parts = []
    for raw in shown:
        raw  = re.sub(r'\s+', ' ', raw).strip()
        abbr = _abbrev_one(raw)
        if _is_primary(raw.replace('{', '').replace('}', '')):
            parts.append(f'<u>{_esc(abbr)}</u>')
        else:
            parts.append(_esc(abbr))
    result = ', '.join(parts)
    if truncated:
        result += ' et al.'
    return result

# ---------------------------------------------------------------------------
# Venue abbreviation
# ---------------------------------------------------------------------------

_ABBREV_MAP = [
    (re.compile(r'\bTransactions on\b',   re.I), 'Trans.'),
    (re.compile(r'\bConference on\b',     re.I), 'Conf.'),
    (re.compile(r'\bJournal of\b',        re.I), 'J.'),
    (re.compile(r'\bInternational\b',     re.I), "Int'l"),
    (re.compile(r'\b and \b',             re.I), ' & '),
]

def _shorten_venue(s: str) -> str:
    for pat, repl in _ABBREV_MAP:
        s = pat.sub(repl, s)
    return s

# ---------------------------------------------------------------------------
# Entry type: for within-year sorting (conf → journal → book)
# ---------------------------------------------------------------------------

_CONF_TYPES = {'inproceedings', 'inproceedgins', 'conference'}
_JOUR_TYPES = {'article'}

def _entry_kind(e: dict) -> int:
    t = (e.get('ENTRYTYPE') or '').lower().strip()
    if t in _CONF_TYPES: return 0
    if t in _JOUR_TYPES: return 1
    return 2

# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------

FS   = 10.5   # body font size
LEAD = 14.5   # leading

S_ENTRY = ParagraphStyle('Entry',
    fontName=F_BODY, fontSize=FS, leading=LEAD,
    textColor=C_INK, alignment=TA_JUSTIFY,
    leftIndent=NUM_W, firstLineIndent=-NUM_W,
    spaceBefore=0, spaceAfter=4,
)

# ---------------------------------------------------------------------------
# Canvas callbacks
# ---------------------------------------------------------------------------

def _draw_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(C_HDR)
    canvas.setLineWidth(0.4)
    y_rule = MB + FOOTER_H - 1.5*mm
    canvas.line(ML, y_rule, PAGE_W - MR, y_rule)
    canvas.setFont(F_ITAL, 8)
    canvas.setFillColor(C_LIGHT)
    canvas.drawString(ML, MB + 1.5*mm, f"{AUTHOR_NAME}  ·  Publication List")
    canvas.drawRightString(PAGE_W - MR, MB + 1.5*mm, str(doc.page))
    canvas.restoreState()

def _draw_first_page(canvas, doc):
    _draw_page(canvas, doc)
    canvas.saveState()
    top = PAGE_H - MT

    canvas.setStrokeColor(C_HDR)
    canvas.setLineWidth(2.5)
    canvas.line(ML, top + 1*mm, PAGE_W - MR, top + 1*mm)

    canvas.setFont(F_BODY, 22)
    canvas.setFillColor(C_HDR)
    canvas.drawString(ML, top - 10*mm, "Publication List")

    canvas.setFont(F_ITAL, 10.5)
    canvas.setFillColor(C_LIGHT)
    total = getattr(doc, '_entry_count', '')
    canvas.drawString(ML, top - 17*mm, f"{total} publications  ·  {AUTHOR_NAME}")

    canvas.setStrokeColor(C_TITLE)
    canvas.setLineWidth(0.5)
    canvas.line(ML, top - HEADER_H + 2*mm, PAGE_W - MR, top - HEADER_H + 2*mm)
    canvas.restoreState()

# ---------------------------------------------------------------------------
# Frame builder
# ---------------------------------------------------------------------------

def _make_frames(frame_h: float) -> list:
    return [Frame(ML, FRAME_Y, BODY_W, frame_h,
                  leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)]

# ---------------------------------------------------------------------------
# Entry rendering
# ---------------------------------------------------------------------------

def _entry_para(e: dict, n: int) -> Paragraph:
    """Return a single hanging-indent Paragraph:  N.  Authors (Year), "Title", Venue."""
    title_raw  = apply_title_case((e.get('title') or 'Untitled').strip())
    title      = _esc(_clean_title(title_raw))
    authors    = fmt_authors_pdf(e.get('author') or '')
    year_str   = _esc((e.get('year') or '').strip())
    note       = note_clean(e.get('note') or '')

    venue_full  = _shorten_venue(_esc(pub_venue_str(e)))
    venue_clean = re.sub(r'\s*\(\d{4}\)\s*$', '', venue_full).strip()

    note_markup = (
        f' <font color="{C_NOTE.hexval()}">[{_esc(note)}]</font>'
        if note else ''
    )
    year_paren = f' ({year_str})' if year_str else ''

    entry_markup = (
        f'<font color="{C_NUM.hexval()}" size="8">{n}.</font>  '
        f'{authors}{year_paren}, '
        f'\u201c<font color="{C_TITLE.hexval()}">{title}</font>\u201d'
        f'{note_markup}'
        + (f', <i>{venue_clean}</i>.' if venue_clean else '.')
    )
    return Paragraph(entry_markup, S_ENTRY)

# ---------------------------------------------------------------------------
# Document build
# ---------------------------------------------------------------------------

def build_pdf(entries: list, output_path: str):
    tpl_first = PageTemplate(id='First',
        frames=_make_frames(FIRST_FRAME_H), onPage=_draw_first_page)
    tpl_later = PageTemplate(id='Later',
        frames=_make_frames(FULL_FRAME_H),  onPage=_draw_page)

    doc = BaseDocTemplate(
        output_path, pagesize=A4,
        pageTemplates=[tpl_first, tpl_later],
        title=f"Publications — {AUTHOR_NAME}",
        author=AUTHOR_NAME,
        subject="Academic publication list",
        creator="generate_pdf.py",
    )
    doc._entry_count = len(entries)

    story = [NextPageTemplate('Later')]

    # Group by year; within each year: conferences → journals → books
    years_dict: OrderedDict = OrderedDict()
    for e in entries:
        yr = (e.get('year') or 'Unknown').strip()
        years_dict.setdefault(yr, []).append(e)

    # Sort within each year by type first
    for yr in years_dict:
        years_dict[yr].sort(key=_entry_kind)

    # Flatten into display order, then assign numbers (last entry = 1)
    ordered = [(yr, e) for yr, yr_entries in years_dict.items() for e in yr_entries]
    total = len(ordered)
    for i, (yr, e) in enumerate(ordered):
        n = total - i  # newest first gets highest number; oldest last gets 1
        story.append(_entry_para(e, n))

    # Timestamp at end of last page
    ts = datetime.now().strftime("Generated %d %B %Y, %H:%M")
    S_TS = ParagraphStyle('TS', fontName=F_ITAL, fontSize=8, leading=12,
                          textColor=C_LIGHT, alignment=TA_LEFT, spaceBefore=18)
    story.append(Paragraph(ts, S_TS))

    print(f"  Writing {output_path}…")
    doc.build(story)
    print(f"  Done — {doc.page} pages.")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Parsing bib file…")
    entries = parse_bib()
    print(f"  {len(entries)} entries found")
    build_pdf(entries, OUTPUT_PDF)
    print(f"\nPDF saved to: {OUTPUT_PDF}")

if __name__ == "__main__":
    main()
