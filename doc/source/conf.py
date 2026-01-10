# Configuration file for the Sphinx documentation builder.
import os
import sys

from docutils import nodes

try:
    from ftw.patch._version import __version__
    version = __version__
    release = __version__
except ImportError:
    version = '1.0'  # Fallback, damit ePub nicht meckert
    release = '1.0.0'

# -- Custom Roles and Components ---------------------------------------------
def ftwpatchopt_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    """Custom role for monospace text styling."""
    node = nodes.literal(rawtext, text, classes=['ftwpatchopt'])
    return [node], []

def setup(app):
    """Register custom components during the Sphinx setup process."""
    app.add_role('ftwpatchopt', ftwpatchopt_role)


# -- Project information -----------------------------------------------------
project = "FTW Patch"
copyright = "2025, Fitzz TeΧnik Welt"
author = "Fitzz TeΧnik Welt"
html_show_copyright = True

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinxarg.ext",
    "autoclasstoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    'sphinx_design',
]

templates_path = ["_templates", "_templates/autosummary"]
exclude_patterns = []
language = "en"
maximum_signature_line_length= 120
toc_object_entries_show_parents='hide'
suppress_warnings=[
    'app.add_directive',
    'autosummary.import_cycle',
]

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_book_theme"
html_static_path = ['_static']
html_css_files = ['custom_html.css']
toc_object_entries = True
toc_object_entries_show_parents = 'hide'
html_theme_options = { 
    "icon_links": [
        {
            "name": "General Index",
            "url": "/genindex",
            "icon": 'https://raw.githubusercontent.com/fortawesome/Font-Awesome/6.x/svgs/solid/book.svg',
            "type": "url",
            "attributes": {
               "target": "_self",
            },
        },
        {
            "name": "Module Index",
            "url": "/py-modindex",
            "icon": 'https://raw.githubusercontent.com/fortawesome/Font-Awesome/6.x/svgs/solid/code.svg',
            "type": "url",
            "attributes": {
               "target": "_self",
            },
        },
        {
            "name": "About",
            "url": "/about",
            "icon": "https://raw.githubusercontent.com/fortawesome/Font-Awesome/6.x/svgs/solid/circle-info.svg",
            "type": "url",
            "attributes": {
                "target": "_self"
            },
        },
    ],
    "show_toc_level": 5, 
    "show_navbar_depth": 2, 
    "home_page_in_toc": True,
}
# intersphinx configuration
intersphinx_mapping = {"python": (f"https://docs.python.org/{sys.version_info.major}.{sys.version_info.minor}",
                                    None)}
# -- Options for ePub output -------------------------------------------------
epub_theme = 'epub'
epub_basename = 'FTW_Patch_Handbuch'
epub_title = project
epub_author = author
epub_publisher = author
epub_identifier = 'https://github.com/fitzz-ftw/ftw-patch.git'
epub_scheme = 'URL'
epub_css_files = ['custom_epub.css']
# Fügt den Index und Modulindex zum internen Guide hinzu
epub_use_index = True  # Erlaubt die Generierung des Index

# Dies erzwingt die Aufnahme in das Inhaltsverzeichnis des Readers
epub_tocscope = 'default'
epub_tocdepth = 3


epub_exclude_files = [
    '_static/fonts/GUST-FONT-LICENSE.txt',
    '.buildinfo.bak'
]

# -- Autodoc / Autosummary configuration -------------------------------------
autodoc_typehints = "description"
autodoc_class_signature = "separated"
autodoc_typehints_description_target = "documented_params"
autodoc_default_options = {
    "members": True,
    #    'special-members': False,
    #    'private-members': False,
    #    'inherited-members': False,
    # 'undoc-members': True,
    "exclude-members": "__weakref__, __new__",
    "class-doc-from": "class",
}

# autosummary configuration
autosummary_generate = True
autosummary_generate_overwrite = True
autosummary_imported_members = False
autosummary_ignore_module_all = False
autosummary_context = {}

class_extention_context = {
    "class_inc": "classinc",
    "module_inc": "moduleinc",
    "function_inc": "funcinc",
    "class_show_inheritance": True,
    "excl_class_show_inheritance": [
    ],
    "autoclass_toc": True,
}

autosummary_context.update(class_extention_context)


# coverage configuration
coverage_statistics_to_stdout = True
coverage_show_missing_items = True

# Python domain configuration
add_module_names = False
python_display_short_literal_types = True

