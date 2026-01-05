# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath('.'))
project = "FTW Patch"
copyright = "2025, Fitzz TeXnik Welt"
author = "Fitzz TeXnik Welt"
html_show_copyright = True

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "autoclasstoc",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_annotation",
    "sphinx.ext.doctest",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinxarg.ext",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    'sphinx_design',
    # "sphinxcontrib-mermaid",
    # "sphinxcontrib-plantuml",
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
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
# html_theme = 'classic'
# Configuration for python_docs_theme
# html_theme = "python_docs_theme"
# html_static_path = ["_static"]
# html_show_sourcelink = True
# html_theme_options = {
#     "sidebarwidth": "300",
#     "collapsiblesidebar": False,
#     "stickysidebar": True,
#     "navigation_with_keys": True,
#     "rightsidebar": False,
# }
# html_sidebars = {
#     "devel/**": ["searchbox.html", "globaltoc.html", "relations.html", "mymodul.html",
#                 "sourcelink.html"],
#     "*": ["searchbox.html", "globaltoc.html", "relations.html", "sourcelink.html"],
# }

# ##############
# # Configuration for read_the_docs
# html_theme = "sphinx_rtd_theme"
# html_static_path = ["_static"]
# html_show_sourcelink = True
# html_theme_options = {
#     "collapse_navigation": True,  # Zeigt Unterpunkte in der Sidebar an
#     "sticky_navigation": True,     # Sidebar bleibt beim Scrollen fixiert
#     "navigation_depth": 4,         # Tiefe der Menüstruktur
#     #"display_version": True,       # Zeigt die Projektversion oben links an
#     "includehidden": True,
#     "titles_only": False,
# }
# def setup(app):
#     app.add_css_file("custom.css")
# ##########

# ################
# # Configuration for furo
# html_theme = "furo"

# # Furo braucht kaum Optionen, um gut auszusehen
# html_theme_options = {
#     "sidebar_hide_name": False,
#     "navigation_with_keys": True,
# }
# ########

#################
# Configuration for pydata_sphinx_them
#                   ^^^^^^^^^^^^^^^^^^^
# html_theme = "pydata_sphinx_theme"

# html_theme_options = {
#     "logo": {
#         "text": "FTW Patch",
#     },
#     "show_nav_level": 2,
#     "show_prev_next": True,
#     "navbar_align": "left",
#     "secondary_sidebar_items": ["page-toc", "edit-this-page"],
#     "navbar_persistent": ["search-button"],
#     "header_links_before_dropdown": 5,
#     "icon_links": [
#         {
#             "name": "Index",
#             "url": "genindex.html", # Verweist auf den General Index
#             "icon": "fa-solid fa-list",
#         },
#     ],
# }

# html_sidebars = {
#   "**": ["sidebar-nav-bs"]
# }

# html_theme_options.update({
#     "external_links": [], # Sicherstellen, dass nichts fälschlich als extern gilt
# })
# ##########

#################
# Configuration for sphinx_book_theme
#                   ^^^^^^^^^^^^^^^^^
html_theme = "sphinx_book_theme"
toc_object_entries = True
toc_object_entries_show_parents = 'hide'
html_theme_options = { "show_toc_level": 4, 
    "show_navbar_depth": 1, 
    "home_page_in_toc": True }

# intersphinx configuration

intersphinx_mapping = {"python": (f"https://docs.python.org/{sys.version_info.major}.{sys.version_info.minor}",
                                    None)}

# autodoc and  autoclasstoc configuration
# autoclass_content = "class" #"both" see:
#               autodoc_default_options:'class-doc-from'
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

# doctest configuration
doctest_global_setup = """
in_sphinx=True
"""
# mermaid extention configuration
#
# 'html', 'png' oder 'svg'
#mermaid_output_format='html'
#mermaid_js = 'https://unpkg.com/mermaid/dist/mermaid.min.js'


# plantuml
#plantuml="java -jar <Pfad zum PlantUML-JAR>"
# 'png' oder 'svg'
#plantuml_output_format='png'
#plantuml_syntax_highlighting = 'html'

