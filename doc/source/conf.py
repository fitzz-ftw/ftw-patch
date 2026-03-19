# Configuration file for the Sphinx documentation builder.
import importlib
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Sequence, cast

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.misc import Include, adapt_path
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

class IncludeIfExists(Include):
    """
    A smart include guard directive.
    If the file exists, it is included with ALL provided options.
    If it doesn't exist, the document remains clean without errors.
    """

    def run(self)-> Sequence[Node]:
        path = directives.path(self.arguments[0])
        if path.startswith('<') and path.endswith('>'):
            path = '/' + path[1:-1]
            root_prefix = self.standard_include_path
        else:
            root_prefix = self.state.document.settings.root_prefix
        path = adapt_path(path,
                          cast(str,self.state.document.current_source),
                          root_prefix)
        exists:bool =Path(path).exists()
        if not exists:
            return []

        return super().run()

def setup(app):
    """Register custom components during the Sphinx setup process."""
    app.add_role('ftwpatchopt', ftwpatchopt_role)
    app.add_role("person", person_role)
    app.add_directive("include-if-exists", IncludeIfExists)


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
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinxcontrib.mermaid",
]


templates_path = ["_templates", "_templates/autosummary"]
exclude_patterns = []
maximum_signature_line_length= 120
toc_object_entries_show_parents='hide'
suppress_warnings=[
    'app.add_directive',
    'autosummary.import_cycle',
    'config.cache',
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



# -- Options for Intersphinx
intersphinx_mapping = {
    "python": (f"https://docs.python.org/{sys.version_info.major}.{sys.version_info.minor}", None),
    "platformdirs": ("https://platformdirs.readthedocs.io/en/latest/", None),
}

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
    'special-members': False,
    'private-members': "_ANSI,_color_map",
    #    'inherited-members': False,
    # 'undoc-members': True,
    "exclude-members": "__weakref__,__new__",
    "class-doc-from": "class",
}

#SECTION - Function for Autosummary
def create_mermaid_decision_maker(whitelist:list[str]|None=None, 
                                  blacklist:list[str]|None=None) -> Callable[..., bool]:
    whitelist = whitelist or []
    blacklist = blacklist or []

    def should_render_mermaid(fullname):
        # 1. FAST RETURN: Blacklist (Geringste Kosten)
        # Wenn wir es explizit verboten haben, sofort raus.
        if fullname in blacklist:
            return False

        # 2. FAST RETURN: Whitelist (Geringe Kosten)
        # Wenn wir wissen, dass es gewollt/möglich ist, sofort ok.
        if fullname in whitelist:
            return True

        # 3. HEAVY LIFTING: Import & Analyse (Hohe Kosten)
        # Erst wenn die Listen keine Antwort liefern, werfen wir die Import-Maschine an.
        try:
            # Trennung von Modul und Attribut
            if "." not in fullname:
                return False

            module_name, class_name = fullname.rsplit(".", 1)
            module = importlib.import_module(module_name)
            obj = getattr(module, class_name)

            if isinstance(obj, type):
                # Technische Prüfung der Basisklassen
                return any(b.__name__ != "object" for b in obj.__bases__)

            return False
        except (ImportError, AttributeError, ValueError):
            return False

    return should_render_mermaid
#!SECTION

#SECTION - Options for Autosummary 
autosummary_generate = True
autosummary_generate_overwrite = True
autosummary_imported_members = False
autosummary_ignore_module_all = True
autosummary_context = {}

inherit_diagramm: list[str] = ["fitzzftw.patch.lines", 'fitzzftw.patch.exceptions']
exclude_inherit_diagramm: list[str] = []

class_extention_context = {
    "class_inc": "classinc",
    "module_inc": "moduleinc",
    "function_inc": "funcinc",
    "class_show_inheritance": True,
    "excl_class_show_inheritance": [
        "LineLike",
    ],
    "excl_class_show_inheritance_member": {
        "LineLike": [],
    },
    "include_private_members": {
        "LineLike": [
            "_color_map",
        ],
    },
    "autoclass_toc": True,
    "inheritence_diagram": create_mermaid_decision_maker(
        inherit_diagramm, exclude_inherit_diagramm
    ),
}

autosummary_context.update(class_extention_context)

#!SECTION

# -- Options for Documentationcoverage
coverage_statistics_to_stdout = True
coverage_show_missing_items = True
coverage_modules = ["fitzzftw.patch",
                    "fitzzftw.baselib",
                    "fitzzftw.develtool"]
coverage_ignore_modules = [
    r".*_version",
    r".*testinfra.*",
    r".*converter.*",
]

# -- Options for (Python) domain
add_module_names = False
python_display_short_literal_types = True

