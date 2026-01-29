"""Sphinx configuration for Start Green Stay Green documentation.

This configuration generates Sphinx documentation from Google-style docstrings
using the Furo theme. Used by ReadTheDocs for hosted documentation.
"""

from pathlib import Path
import sys

# Add parent directory to path so we can import the package
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Project information
project = "Start Green Stay Green"
project_copyright = "2026, Start Green Stay Green Contributors"
copyright = project_copyright  # noqa: A001 - Sphinx requires this builtin shadow
author = "Start Green Stay Green Team"

# Read version from package
try:
    from start_green_stay_green import __version__

    release = __version__
except ImportError:
    release = "0.1.0"

version = ".".join(release.split(".")[:2])

# General configuration
extensions = [
    "sphinx.ext.autodoc",  # Include documentation from docstrings
    "sphinx.ext.intersphinx",  # Link to other Sphinx documentation
    "sphinx.ext.napoleon",  # Google-style docstrings
    "sphinx.ext.viewcode",  # Link to source code
    "sphinx.ext.todo",  # Support for TODO directive
    "myst_parser",  # Markdown support
]

# Source file extensions
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Docstring style
autodoc_typehints = "description"
autodoc_member_order = "bysource"

# Include private members in documentation (controlled per module)

# Master document
master_doc = "index"

# Markdown support (using MyST parser)
myst_enable_extensions = [
    "colon_fence",
    "dollarmath",
    "linkify",
]

# Theme configuration
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": True,
    "display_version": True,
    "prev_next_buttons_location": "both",
    "style_external_links": False,
    "style_nav_header_background": "#2980B9",
    # Sidebar options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# HTML output options
html_static_path: list[str] = []
html_logo = None
html_favicon = None
html_title = f"{project} {version}"

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# LaTeX output configuration
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
}

# Paths
exclude_patterns = [
    "_build",
    "**.ipynb_checkpoints",
    "venv",
    ".venv",
]

# Language
language = "en"

# Warnings
suppress_warnings = [
    "app.warn_css",
    "app.warn_javascript",
]

# Linkcheck
linkcheck_ignore = [
    r"https://github\.com/Geoffe-Ga/start_green_stay_green/issues/\d+",
    r"https://github\.com/Geoffe-Ga/start_green_stay_green/pull/\d+",
]

# Use nitpicky mode (stricter)
# Keep current directory when including
keep_warnings = False

# Show TODO directives in output
todo_include_todos = False

# Additional configuration
# (Add extensions and settings as needed)

# Napoleon extension for Google-style docstring formatting
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_keyword = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc options
autodoc_preserve_defaults = True
autodoc_class_signature = "mixed"

# Additional settings for better documentation
root_doc = "index"
project_urls = {
    "GitHub": "https://github.com/Geoffe-Ga/start_green_stay_green",
    "Documentation": "https://start-green-stay-green.readthedocs.io",
    "Issues": "https://github.com/Geoffe-Ga/start_green_stay_green/issues",
}
