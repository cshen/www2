"""
config.py — User-facing configuration for generate.py.

Edit the values here to customise the site without touching generate.py.
"""

# Input / output paths
BIB_FILE     = "cs.bib"
ABSTRACT_DIR = "abstract"
DETAILS_DIR  = "details"

# Name highlighted as the primary author throughout the site
AUTHOR_NAME  = "Chunhua Shen"

# Base URL of the deployed site (used for share buttons on detail pages).
# Include trailing slash. Leave blank ("") to disable share buttons.
SITE_BASE_URL = "https://cshen.github.io/"

# GitHub repository URL for the "Report issue" button on detail pages.
# Set to the repo URL (e.g. "https://github.com/cshen/cshen.github.io").
# Leave blank ("") to disable the report-issue button entirely.
GITHUB_REPO_URL = "https://github.com/cshen/cshen.github.io"

# Rule 11: fixed primary venue filter buttons shown at the top of the page
PRIMARY_VENUES = ["CVPR", "ICCV", "ECCV", "ICML", "NeurIPS", "ICLR", "TPAMI", "IJCV"]

# Venue prestige ordering used to sort papers within each year
# (lower index = higher prestige; venues not listed are sorted last)
VENUE_ORDER = [
    "CVPR", "ICCV", "ECCV", "NeurIPS", "ICML", "ICLR",
    "TPAMI", "IJCV", "SIGGRAPH", "KDD", "AAAI", "IJCAI",
    "JMLR"
]
