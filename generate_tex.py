#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["bibtexparser"]
# ///
"""
generate_tex.py — Generate a standalone XeLaTeX publication list from cs.bib.

Reads cs.bib → writes cshen_papers_out.tex with all content inlined.
No external files or bin/ directory required.

Usage:
    python3 generate_tex.py [output.tex]

Compile with:
    xelatex cshen_papers_out.tex
"""

import re
import sys
from urllib.parse import quote_plus

import bibtexparser
from bibtexparser.bparser import BibTexParser

from config import AUTHOR_NAME, BIB_FILE

OUTPUT_TEX = sys.argv[1] if len(sys.argv) > 1 else "cshen_papers_out.tex"

# ---------------------------------------------------------------------------
# Venue classification sets  (matched against the `venue` bib field, lowercase)
# ---------------------------------------------------------------------------

TOP_CONF_VENUES = {
    'cvpr', 'iccv', 'eccv', 'icml', 'neurips', 'nips', 'iclr', 'kdd',
}
MAJOR_CONF_VENUES = {
    'aaai', 'ijcai', 'icra', 'bmvc', 'acmmm', 'mm', 'miccai', 'siggraph',
    'ecal', 'acl', 'emnlp', 'naacl', 'findings',
}


# ---------------------------------------------------------------------------
# BibTeX parsing
# ---------------------------------------------------------------------------

def parse_bib() -> list:
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    with open(BIB_FILE, encoding='utf-8') as f:
        db = bibtexparser.load(f, parser=parser)
    return db.entries

# ---------------------------------------------------------------------------
# Author formatting
# ---------------------------------------------------------------------------

_PARTICLES = frozenset({
    'van', 'de', 'den', 'der', 'von', 'di', 'del', 'le', 'la', 'los', 'las',
    'ter', 'ten', 'af', 'da', 'dos', 'du', 'bin', 'binte',
})


def _abbrev_one(raw: str) -> str:
    """Abbreviate a single author name to 'F.~Last' form."""
    raw = re.sub(r'[{}]', '', raw).strip()
    raw = re.sub(r'\s+', ' ', raw)
    if not raw:
        return ''
    if ',' in raw:
        idx     = raw.index(',')
        last    = raw[:idx].strip()
        firsts  = raw[idx + 1:].strip()
        initials = ''.join(
            w[0].upper() + '.' for w in firsts.split() if w and w[0].isalpha()
        )
        return f"{initials}~{last}" if initials else last

    tokens = raw.split()
    if len(tokens) == 1:
        return tokens[0]
    if len(tokens) == 2:
        return f"{tokens[0][0].upper()}.~{tokens[1]}"
    # Find where the last-name portion starts
    last_start = len(tokens) - 1
    for i in range(1, len(tokens)):
        if tokens[i][0].islower() or tokens[i].lower() in _PARTICLES:
            last_start = i
            break
    first_tokens = tokens[:last_start]
    last_tokens  = tokens[last_start:]
    initials = ''.join(t[0].upper() + '.' for t in first_tokens if t and t[0].isalpha())
    last     = ' '.join(last_tokens)
    return f"{initials}~{last}" if initials else last


def _is_primary(raw: str) -> bool:
    clean = re.sub(r'[{}]', '', raw).strip()
    return clean in (AUTHOR_NAME, 'Shen, Chunhua')


def fmt_authors(author_str: str) -> str:
    if not author_str:
        return ''
    names = re.split(r'\s+and\s+', author_str.strip(), flags=re.IGNORECASE)
    parts = []
    for name in names:
        abbr = _abbrev_one(name)
        if _is_primary(name):
            parts.append(r'\highlight{' + abbr + '}')
        else:
            parts.append(abbr)
    return ', '.join(parts)

# ---------------------------------------------------------------------------
# Title / venue helpers
# ---------------------------------------------------------------------------

def clean_field(s: str) -> str:
    """Collapse whitespace; keep LaTeX markup intact."""
    return re.sub(r'\s+', ' ', (s or '')).strip()


def venue_of(e: dict) -> str:
    return (e.get('venue') or '').strip().lower()


def classify(e: dict) -> str:
    entrytype = (e.get('ENTRYTYPE') or '').lower()
    v = venue_of(e)
    if entrytype == 'article':
        return 'journal'
    if v in TOP_CONF_VENUES:
        return 'top_conf'
    if v in MAJOR_CONF_VENUES:
        return 'major_conf'
    return 'other_conf'


_VENUE_ABBREVS = [
    (re.compile(r'\bConference\b'),    'Conf.'),
    (re.compile(r'\bJournal\b'),       'J.'),
    (re.compile(r'\bTransactions\b'),  'Trans.'),
    (re.compile(r'\bInternational\b'), 'Int.'),
    (re.compile(r'\bEuropean\b'),      'Eur.'),
    (re.compile(r'\s+and\s+'),         r' \& '),
    # Remove prepositions after abbreviations and add LaTeX non-sentence space
    (re.compile(r'Conf\.\s+on\b'),     r'Conf.\\ '),
    (re.compile(r'J\.\s+of\b'),        r'J.\\ '),
    (re.compile(r'Trans\.\s+on\b'),    r'Trans.\\ '),
    (re.compile(r'Int\.\s+Conf\.'),    r'Int.\\ Conf.'),
    (re.compile(r'Int\.\s+J\.'),       r'Int.\\ J.'),
]


def shorten_venue(s: str) -> str:
    for pat, repl in _VENUE_ABBREVS:
        s = pat.sub(repl, s)
    return s


def _plain_text(s: str) -> str:
    """Strip LaTeX markup to plain text (used for URL query building)."""
    s = re.sub(r'\$[^$]+\$', '', s)          # remove math spans
    s = re.sub(r'\\[a-zA-Z]+\s*', '', s)     # remove \commands
    s = re.sub(r'[{}]', '', s)               # remove braces
    return re.sub(r'\s+', ' ', s).strip()


def _scholar_url(title: str, author_str: str) -> str:
    """Build a Google Scholar search URL for a paper."""
    plain_title   = _plain_text(title)
    # Full author names (brace-stripped), comma-separated
    raw_names     = re.split(r'\s+and\s+', (author_str or '').strip(), flags=re.IGNORECASE)
    plain_authors = ', '.join(re.sub(r'[{}]', '', n).strip() for n in raw_names)
    query = quote_plus(f"{plain_title} {plain_authors}")
    return f"http://www.google.com/search?lr=&ie=UTF-8&oe=UTF-8&q={query}"


def venue_tex(e: dict) -> str:
    """Return the LaTeX venue/source string for an entry."""
    entrytype = (e.get('ENTRYTYPE') or '').lower()
    if entrytype == 'article':
        journal = shorten_venue(clean_field(e.get('journal') or e.get('booktitle') or ''))
        vol     = clean_field(e.get('volume') or '')
        pages   = clean_field(e.get('pages') or '')
        s = r'\emph{' + journal + '}'
        if vol:
            s += f', {vol}'
        if pages:
            s += f': {pages}'
        return s
    else:
        bt = shorten_venue(clean_field(e.get('booktitle') or ''))
        return r'In: \emph{Proc.\ ' + bt + '}'


def make_entry_tex(e: dict, first: bool = False) -> str:
    """Render one bib entry as a LaTeX paragraph line."""
    year       = clean_field(e.get('year') or '')
    title      = clean_field(e.get('title') or 'Untitled')
    author_str = e.get('author') or ''
    authors    = fmt_authors(author_str)
    venue      = venue_tex(e)
    year_paren = f' ({year}),' if year else ','
    noindent   = r'\noindent ' if first else ''

    url          = _scholar_url(title, author_str)
    linked_title = f'\\href{{{url}}}{{``{title},{{}}\'\'}}'

    return (
        f'\\years{{{year}}} {noindent}{authors}{year_paren}\n'
        f'{linked_title}\n'
        f'{venue}.\n'
        f'\n'
        f'\\medskip\n'
    )

# ---------------------------------------------------------------------------
# Sort helpers
# ---------------------------------------------------------------------------

def _sort_key(e: dict):
    try:
        yr = int(e.get('year') or 0)
    except ValueError:
        yr = 0
    return -yr   # newest first


# ---------------------------------------------------------------------------
# LaTeX preamble  (based on cshen_papers.tex; marginnote from system package)
# ---------------------------------------------------------------------------

PREAMBLE = r"""%------------------------------------
% Chunhua Shen's Publications in LaTeX
% Generated by generate_tex.py from cs.bib
%------------------------------------
%!TEX TS-program = xelatex
%!TEX encoding = UTF-8 Unicode

\documentclass[9pt, a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{amssymb,amsmath}
\usepackage{graphicx}

\usepackage{ifxetex,ifluatex}
\ifnum 0\ifxetex 1\fi\ifluatex 1\fi=0 % if pdftex
  \usepackage[utf8]{inputenc}
\else % if luatex or xelatex
  \usepackage{fontspec}
  \ifxetex
    \usepackage{xltxtra,xunicode}
  \fi
  \defaultfontfeatures{Mapping=tex-text,Scale=MatchLowercase}
  \newcommand{\euro}{€}
\fi
\IfFileExists{microtype.sty}{\usepackage{microtype}}{}

% DOCUMENT LAYOUT
\usepackage[top=.5in, bottom=.5in, left=1.36in, right=1in]{geometry}
\geometry{a4paper, textwidth=5.5in, textheight=8.5in, marginparsep=7pt, marginparwidth=.6in}
\setlength\parindent{0in}

\usepackage[]{metalogo}

% FONTS
\usepackage{xunicode}
\usepackage{xltxtra}
\defaultfontfeatures{Ligatures=TeX}
\setromanfont[Ligatures={Common},Numbers={OldStyle}]{Adobe Caslon Pro}
\setmonofont[Scale=0.7]{Monaco}
\setsansfont[Mapping=tex-text,Scale=0.8]{Calibri}

% ---- CUSTOM AMPERSAND
\newcommand{\amper}{{\fontspec[Scale=.8]{Adobe Caslon Pro}\selectfont\itshape\&}}

% ---- MARGIN YEARS
\usepackage{marginnote}
\newcommand{\years}[1]{\marginnote{\scriptsize #1}}
\renewcommand*{\raggedleftmarginnote}{}
\setlength{\marginparsep}{7pt}
\reversemarginpar
\let\id\years

% HEADINGS
\usepackage{sectsty}
\usepackage[normalem]{ulem}
\sectionfont{\rmfamily\mdseries\Large}
\subsectionfont{\rmfamily\mdseries\scshape\normalsize}
\subsubsectionfont{\rmfamily\bfseries\upshape\normalsize}

\usepackage{xcolor}
\usepackage[]{ulem}
\def\highlight{\uline}

\usepackage{microtype}

% Current time / date macros
\newcount\timehh\timehh=\time
\divide\timehh by 60
\newcount\timemm\timemm=\time
\count255=\timehh
\multiply\count255 by -60
\advance\timemm by \count255
\newif\iftimePM
\ifnum\timehh>11 \timePMtrue\else\timePMfalse\fi
\ifnum\timehh<1 \advance\timehh by 12\fi
\ifnum\timehh>12 \advance\timehh by -12\fi
\def\now{\number\timehh:\ifnum\timemm<10 0\fi\number\timemm
         \iftimePM {$\,$pm.}  \else {$\,$am.}  \fi}
\edef\today{\number\day$\cdot$\number\month$\cdot$\number\year}

\hyphenpenalty=1750
\hyphenation{con-vo-lu-t-i-o-n-a-l cro-ss-con-vo-lu-t-i-on-al-l-a-y-er D-I-C-T-A C-V-P-R I-C-C-V}

% PDF SETUP
\usepackage[bookmarks, colorlinks, breaklinks,
  pdftitle={Chunhua Shen - Publications},
  pdfauthor={Chunhua Shen}]{hyperref}
\hypersetup{linkcolor=blue,citecolor=blue,filecolor=black,urlcolor=blue}

\usepackage{ifthen,xspace}

\pagestyle{empty}
"""

# ---------------------------------------------------------------------------
# Document body builder
# ---------------------------------------------------------------------------

TOP_CONF_BLURB = r"""
{
\begin{itemize}
  \itemsep -.12cm
\footnotesize
\item \emph{Proc.\ Annual Conf.\ Neural Information Processing Systems (NeurIPS)}
\item \emph{Proc.\ Int.\ Conf.\ Machine Learning (ICML)}
\item \emph{Proc.\ IEEE Conf.\ Computer Vision \& Pattern Recognition (CVPR)}
\item \emph{Proc.\ Int.\ Conf.\ Computer Vision (ICCV)}
\item \emph{Proc.\ European Conf.\ Computer Vision (ECCV)}
\item \emph{Proc.\ Int.\ Conf.\ Learning Representations (ICLR)}
\item \emph{Proc.\ ACM SIGKDD Conf.\ Knowledge Discovery and Data Mining (KDD)}
\end{itemize}
}
"""

MAJOR_CONF_BLURB = r"""
{
\begin{itemize}
  \itemsep -.12cm
\footnotesize
\item \emph{Proc.\ AAAI Conf.\ Artificial Intelligence (AAAI)}
\item \emph{Proc.\ Findings Association for Computational Linguistics (ACL/EMNLP)}
\item \emph{Proc.\ Int.\ Joint Conf.\ Artificial Intelligence (IJCAI)}
\item \emph{Proc.\ IEEE Int.\ Conf.\ Robotics \& Automation (ICRA)}
\item \emph{Proc.\ British Machine Vision Conf.\ (BMVC)}
\item \emph{Proc.\ ACM Int.\ Conf.\ Multimedia (ACM MM)}
\item \emph{Proc.\ Int.\ Conf.\ Medical Image Computing and Computer Assisted Intervention (MICCAI)}
\item \emph{Proc.\ ACM Special Interest Group on Computer Graphics and Interactive Techniques Conf.\ (SIGGRAPH)}
\end{itemize}
}
"""


def build_tex(entries: list) -> str:
    journals   = sorted([e for e in entries if classify(e) == 'journal'],    key=_sort_key)
    top_confs  = sorted([e for e in entries if classify(e) == 'top_conf'],   key=_sort_key)
    major_confs= sorted([e for e in entries if classify(e) == 'major_conf'], key=_sort_key)
    other_confs= sorted([e for e in entries if classify(e) == 'other_conf'], key=_sort_key)

    total = len(entries)

    def render_section(items: list) -> str:
        return '\n'.join(make_entry_tex(e, first=(i == 0)) for i, e in enumerate(items))

    doc = PREAMBLE
    doc += '\n% DOCUMENT\n\\begin{document}\n\n'

    doc += f'\\section*{{Refereed Publications ({total})}}\n\n'

    # Journals
    doc += f'\\subsection*{{Refereed journal articles ({len(journals)})}}\n'
    doc += render_section(journals)

    # Top conferences
    doc += '\n\\vspace{-0.15cm}\n'
    doc += (
        f'\\subsection*{{Refereed top conference articles in computer vision '
        f'and machine learning ({len(top_confs)})}}\n'
    )
    doc += TOP_CONF_BLURB
    doc += '\n'
    doc += render_section(top_confs)

    # Major conferences
    doc += '\n\\vspace{-0.15cm}\n'
    doc += (
        f'\\subsection*{{Refereed major conference articles in artificial '
        f'intelligence and robotics ({len(major_confs)})}}\n'
    )
    doc += MAJOR_CONF_BLURB
    doc += '\n'
    doc += render_section(major_confs)

    # Other conferences
    doc += '\n\\vspace{-0.15cm}\n'
    doc += f'\\subsection*{{Refereed other miscellaneous conference articles ({len(other_confs)})}}\n'
    doc += render_section(other_confs)

    # Footer
    doc += r"""
\vfill{}
\begin{center}
{\scriptsize Compiled at: \now \today\ $\cdot$ Typeset in {
\fontspec{Times New Roman}\XeLaTeX{}
using Python script
}\\
\href{https://cshen.github.io}{cshen.github.io}
}
\end{center}

\end{document}
"""
    return doc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Parsing bib file…")
    entries = parse_bib()
    print(f"  {len(entries)} entries found")

    journals    = [e for e in entries if classify(e) == 'journal']
    top_confs   = [e for e in entries if classify(e) == 'top_conf']
    major_confs = [e for e in entries if classify(e) == 'major_conf']
    other_confs = [e for e in entries if classify(e) == 'other_conf']
    print(f"  journals={len(journals)}, top_conf={len(top_confs)}, "
          f"major_conf={len(major_confs)}, other={len(other_confs)}")

    tex = build_tex(entries)
    with open(OUTPUT_TEX, 'w', encoding='utf-8') as f:
        f.write(tex)
    print(f"\nTeX saved to: {OUTPUT_TEX}")
    print("Compile with:  xelatex " + OUTPUT_TEX)


if __name__ == "__main__":
    main()
