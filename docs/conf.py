# conf.py  ────────────────────────────────────────────────────────────────────
# -- Path setup --------------------------------------------------------------
import os
import sys
sys.path.insert(0, os.path.abspath('..'))   # adjust if your Python code is elsewhere

# -- Project information -----------------------------------------------------
project   = 'test_sphinx'
copyright = '2025, Siddhartha'
author    = 'Siddhartha'

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",   # pull docstrings into docs
    "sphinx.ext.napoleon",  # Google / NumPy-style docstrings
    "sphinx.ext.viewcode",  # add links to highlighted source
]

templates_path  = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'  # Read-the-Docs theme

# (Optional) tweak sidebar width, logo, etc.
# html_theme_options = {
#     "navigation_depth": 3,
#     "collapse_navigation": False,
# }
html_static_path = ['_static']
