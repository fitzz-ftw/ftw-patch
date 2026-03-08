# Configuration file for the Sphinx documentation builder.
import os
import sys
from pathlib import Path

from docutils import nodes
from jinja2 import Environment, FileSystemLoader

# Read the Docs liefert uns die Canonical URL direkt!
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

# Falls wir lokal sind, ist die Variable leer, dann setzen wir einen Fallback
if not html_baseurl:
    html_baseurl = "/"


try:
    from fitzzftw.patch._version import __version__
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

def person_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    """Custom role for person names styled as small caps."""
    node = nodes.inline(rawtext, text, classes=["person"])
    return [node], []

def setup(app):
    """Register custom components during the Sphinx setup process."""
    app.add_role('ftwpatchopt', ftwpatchopt_role)
    app.add_role("person", person_role)


# -- Project information -----------------------------------------------------
project = "FTW Patch"
copyright = "2025, Fitzz TeΧnik Welt"
author = "Fitzz TeΧnik Welt"
html_show_copyright = True
language = "en"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinxarg.ext",
    "autoclasstoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
    #  "sphinx_jinja2",
    "sphinx.ext.intersphinx",
    "myst_parser",
    # "sphinx_mdinclude",
]

# source_suffix = {
#     ".rst": "restructuredtext",
#     ".md": "markdown",
# }

templates_path = ["_templates", "_templates/autosummary"]
exclude_patterns = []
maximum_signature_line_length= 120
toc_object_entries_show_parents='hide'
suppress_warnings=[
    'app.add_directive',
    'autosummary.import_cycle',
]




# -- Options for HTML output -------------------------------------------------
# -- New Theme: Nesferitit
html_theme = "sphinx_nefertiti"
html_theme_options = {
    "style": "indigo",
    "documentation_font_size": "1.2rem",
    "header_links": [
        {
            "text": "Index",
            "link": "genindex",
        },
        {
            "text": "List of Modules",
            "link": "py-modindex",
        },
    ],
    "logo": "ftw-initials.svg",
    "logo_height": 40,
    "logo_width": 40*1.2,
    "logo_location": "header",
    # "header_links_in_2nd_row": True,
    "project_name_font": "Fira Sans",
    "doc_headers_font": "Fira Sans",
    "documentation_font": "Fira Sans",
    "sans_serif_font": "Fira Sans",
    "monospace_font": "Fira Code",
}

html_static_path = ["_static"]
html_css_files = ["custom_nefertiti_html.css"]
toc_object_entries = True
toc_object_entries_show_parents = "hide"


# -- Old Theme ----------#
# html_theme = "sphinx_book_theme"
# html_static_path = ['_static']
# html_css_files = ['custom_html.css']
# toc_object_entries = True
# toc_object_entries_show_parents = 'hide'
# html_theme_options = { 
#     "icon_links": [
#         {
#             "name": "General Index",
#             "url": f"{html_baseurl}genindex",
#             "icon": "fa-solid fa-book", # Nutzt die CSS-Klasse statt URL
#             "type": "fontawesome",
#             # "icon": 'https://raw.githubusercontent.com/fortawesome/Font-Awesome/6.x/svgs/solid/book.svg',
#             # "type": "local",
#             "attributes": {
#                "target": "_self",
#             },
#         },
#         {
#             "name": "Module Index",
#             "url": f"{html_baseurl}py-modindex",
#             "icon": 'fa-solid fa-code',
#             "type": "fontawesome",
#             # "icon": 'https://raw.githubusercontent.com/fortawesome/Font-Awesome/6.x/svgs/solid/code.svg',
#             # "type": "url",
#             "attributes": {
#                "target": "_self",
#             },
#         },
#         {
#             "name": "About",
#             "url": f"{html_baseurl}about",
#             "icon": "fa-solid fa-circle-info",
#             "type": "fontawesome",
#             # "icon": "https://raw.githubusercontent.com/fortawesome/Font-Awesome/6.x/svgs/solid/circle-info.svg",
#             # "type": "url",
#             "attributes": {
#                 "target": "_self"
#             },
#         },
#     ],
#     "show_toc_level": 5, 
#     "show_navbar_depth": 2, 
#     "home_page_in_toc": True,
# }

# -- Options for Intersphinx
intersphinx_mapping = {"python": (f"https://docs.python.org/{sys.version_info.major}.{sys.version_info.minor}",



                                  None)}
# -- Options for ePub output -------------------------------------------------

# render_cover("ftwpatch", version)

def render_cover(
    programname: str, version: str, covertemplate: str = "cover.svg"
) -> tuple[str, str]:
    templates_dir = "_templates"
    static_dir = "_static"

    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template(covertemplate)

    # Rendern mit der echten 'release' Variable
    output_path = os.path.join(static_dir, covertemplate)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template.render(version=version, programname=programname))
    return (output_path, "epub-cover.html")


if "epub" in sys.argv:
    epub_cover = render_cover("ftwpatch", version.split("+")[0])


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

auto_exclude_files=[]
if "epub" in sys.argv:
    woff2_files = [str(file_) for file_ in Path().rglob("*.woff2")]
    fira_fonts= [str(file_) for file_ in Path().rglob("fira-*/*")]
    auto_exclude_files=list(set([*woff2_files,*fira_fonts]))


epub_exclude_files = [
    "_static/fonts/GUST-FONT-LICENSE.txt",
    "_static/fonts/OFL.md",
    "_static/fonts/OFL.txt",
    ".buildinfo.bak",
    *auto_exclude_files,
]

# -- Autodoc / Autosummary configuration -------------------------------------
# -- Options for Autodoc
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

# -- Options for Autosummary 
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



# -- Options for Documentationcoverage
coverage_statistics_to_stdout = True
coverage_show_missing_items = True

# -- Options for (Python) domain
add_module_names = False
python_display_short_literal_types = True

