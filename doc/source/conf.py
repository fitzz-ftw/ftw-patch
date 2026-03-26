# Configuration file for the Sphinx documentation builder.
import importlib
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Sequence, cast

from docutils import nodes
from docutils.nodes import Node
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.directives.misc import Include, adapt_path
from jinja2 import Environment, FileSystemLoader
from sphinx.transforms import SphinxTransform

from fitzzftw.patch.ftw_patch import VERBOSITY_LEVELS

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
    """
    Custom role for monospace text styling.

    :param name: The role name used in the document.
    :type name: str
    :param rawtext: The entire markup body.
    :type rawtext: str
    :param text: The argument of the role (the option name).
    :type text: str
    :param lineno: The line number where the role appears.
    :type lineno: int
    :param inliner: The inliner instance.
    :type inliner: docutils.parsers.rst.states.Inliner
    :param options: Directive options for customization.
    :type options: dict
    :param content: The directive content.
    :type content: list
    :return: A tuple containing a list of nodes and a list of system messages.
    :rtype: tuple[list[reference], list[Any]]
    """
    node = nodes.literal(rawtext, text, classes=['ftwpatchopt'])
    return [node], []

def ftwoption_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    """
    Custom Sphinx role to link to CLI options.

    :param name: The role name used in the document.
    :type name: str
    :param rawtext: The entire markup body.
    :type rawtext: str
    :param text: The argument of the role (the option name).
    :type text: str
    :param lineno: The line number where the role appears.
    :type lineno: int
    :param inliner: The inliner instance.
    :type inliner: docutils.parsers.rst.states.Inliner
    :param options: Directive options for customization.
    :type options: dict
    :param content: The directive content.
    :type content: list
    :return: A tuple containing a list of nodes and a list of system messages.
    :rtype: tuple[list[reference], list[Any]]
    """
    inner_node = nodes.literal(rawtext, text, classes=["ftw-opt-link", "custom-option-style"])

    target_id = nodes.make_id(f"opt-{text}")

    ref_node = nodes.reference(rawtext, "", internal=True, refid=target_id)

    ref_node += inner_node

    return [ref_node], []

def person_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    """
    Custom role for person names styled as small caps.

    :param name: The role name used in the document.
    :type name: str
    :param rawtext: The entire markup body.
    :type rawtext: str
    :param text: The argument of the role (the option name).
    :type text: str
    :param lineno: The line number where the role appears.
    :type lineno: int
    :param inliner: The inliner instance.
    :type inliner: docutils.parsers.rst.states.Inliner
    :param options: Directive options for customization.
    :type options: dict
    :param content: The directive content.
    :type content: list
    :return: A tuple containing a list of nodes and a list of system messages.
    :rtype: tuple[list[reference], list[Any]]
    """
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

class VerbosityTableDirective(Directive):
    """
    A custom Sphinx directive to render a verbosity levels table.

    This directive iterates over the ``VERBOSITY_LEVELS`` dictionary and
    generates a docutils table with two columns: 'Level' and 'Description'.

    :return: A list containing the constructed table node.
    :rtype: list[docutils.nodes.table]
    """
    def run(self):
        """
        Process the directive and build the docutils table.

        :return: A list of nodes to be injected into the document.
        :rtype: list[docutils.nodes.node]
        """
        table = nodes.table()
        tgroup = nodes.tgroup(cols=2)
        table += tgroup

        # Define column widths (percentage)
        tgroup += nodes.colspec(colwidth=10)
        tgroup += nodes.colspec(colwidth=90)

        # Build Table Header
        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        # Level column
        entry_lvl = nodes.entry()
        entry_lvl += nodes.paragraph(text="Level")
        # row += nodes.entry("", nodes.paragraph(text="Level"))
        header_row += entry_lvl

        # Description column
        entry_desc = nodes.entry()
        entry_desc += nodes.paragraph(text="Description")
        # row += nodes.entry("", nodes.paragraph(text="Description"))
        header_row += entry_desc

        thead += header_row
        # thead += row


        # Build Table Body
        tbody = nodes.tbody()
        tgroup += tbody

        # Assuming VERBOSITY_LEVELS is a dict {int: str} defined in conf.py
        for lvl, desc in VERBOSITY_LEVELS.items():
            row = nodes.row()
            
            # Level Cell
            c1 = nodes.entry()
            c1 += nodes.paragraph(text=str(lvl))
            row += c1
            # row += nodes.entry("", nodes.paragraph(text=str(lvl)))

            # Description Cell
            c2 = nodes.entry()
            c2 += nodes.paragraph(text=desc)
            row += c2
            # row += nodes.entry("", nodes.paragraph(text=desc))

            tbody += row

        return [table]

def inject_option_anchors(app, doctree):
    """
    Scan the doctree and inject HTML anchors into argparse option groups.

    This function acts as a Sphinx event handler. It identifies all
    ``option_group`` nodes and assigns unique IDs to them, enabling
    internal cross-referencing via the custom :ftwoption: role.

    :param app: The Sphinx application instance.
    :type app: sphinx.application.Sphinx
    :param doctree: The docutils document tree being processed.
    :type doctree: docutils.nodes.document
    """
    docname = app.env.docname
    std = app.env.get_domain("std")

    for node in doctree.traverse(nodes.option_list_item):
        if len(node) < 1 or not isinstance(node[0], nodes.option_group):
            continue

        option_nodes = list(node[0].traverse(nodes.option_string))
        if not option_nodes:
            continue

        opt_text = option_nodes[0].astext()
        anchor_id = f"opt-{opt_text}"

        if anchor_id not in node["ids"]:
            node["ids"].append(anchor_id)

        std.data["labels"][anchor_id] = (docname, anchor_id, opt_text)

class InjectArgparseAnchors(SphinxTransform):
    """
    A transform to inject HTML anchors into argparse option groups.

    This transform scans the document for ``option_group`` nodes and assigns
    a unique ID to each option. It allows direct linking to specific CLI
    flags via the :ftwoption: role.
    """
    def apply(self, **kwargs) -> None:
        """
        Apply the transform to the document tree.

        Iterates through all option groups, generates a clean ID based on
        the longest option string, and registers each option variant as
        a global label in the standard domain.
        """
        std = self.env.get_domain("std")
        docname = self.env.docname

        for node in self.document.findall(nodes.option_group):
            option_nodes = list(node.findall(nodes.option_string))
            if not option_nodes:
                continue

            primary_opt = max([n.astext() for n in option_nodes], key=len)
            clean_id = nodes.make_id(f"opt-{primary_opt}")

            if clean_id not in node["ids"]:
                node["ids"].append(clean_id)

            for opt_node in option_nodes:
                opt_text = opt_node.astext().strip()
                label_key = f"opt-{opt_text}"

                std.data["labels"][label_key] = (docname, clean_id, opt_text)


def setup(app):
    """Register custom components during the Sphinx setup process."""
    app.add_role('ftwpatchopt', ftwpatchopt_role)
    app.add_role("ftwoption", ftwoption_role)
    app.add_role("person", person_role)
    app.add_directive("include-if-exists", IncludeIfExists)
    app.add_directive("verbosity-table", VerbosityTableDirective)
    app.connect("doctree-read", inject_option_anchors)
    app.add_transform(InjectArgparseAnchors)
    InjectArgparseAnchors.default_priority = 10


# -- Project information -----------------------------------------------------
project = "FTW Patch"
copyright = "2025, Fitzz TeΧnik Welt"
author = "Fitzz TeΧnik Welt"
html_show_copyright = True
language = "en"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",       # Zuerst die Basis
    "sphinx.ext.intersphinx",  # Wichtig für Cross-Refs
    "sphinx.ext.autosummary",
    "myst_parser",             # Falls du Markdown nutzt
    "sphinxarg.ext",           # Das "tote Pferd" erst jetzt laden
    "autoclasstoc",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
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
if sys.version_info < (3, 14):
    autodoc_mock_imports = ["annotationlib"]

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

