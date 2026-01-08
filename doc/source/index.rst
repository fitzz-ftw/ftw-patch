
ftw-patch: Unicode-Safe & Whitespace-Aware Patching
===================================================

.. image:: https://img.shields.io/pypi/v/ftw-patch.svg
   :target: https://pypi.org/project/ftw-patch/
   :alt: PyPI version

.. image:: https://readthedocs.org/projects/ftw-patch/badge/?version=latest
   :target: https://ftw-patch.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/badge/coverage-100%25-brightgreen
   :target: https://codecov.io/gh/fitzz-ftw/ftw-patch
   :alt: Code Coverage

.. image:: https://img.shields.io/badge/doc--coverage-100%25-brightgreen
   :target: https://ftw-patch.readthedocs.io/
   :alt: Doc Coverage

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :target: https://github.com/astral-sh/ruff
   :alt: Linting: ruff

.. image:: https://img.shields.io/badge/License-GPL%20v2-blue.svg
   :target: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
   :alt: License: GPL v2

.. 
   .. image:: https://static.pepy.tech/badge/ftw-patch
      :target: https://pepy.tech/project/ftw-patch
      :alt: Downloads

---


:py:mod:`ftw-patch` is a robust Python-based patch utility designed for modern 
development workflows. While traditional patch tools often struggle with different 
line endings, Unicode characters, or minor formatting changes, :py:mod:`ftw-patch` 
provides advanced normalization to make patching reliable and predictable.

Key Features
------------

* **Unicode-Safe:** Native handling of UTF-8 and other encodings without corruption.
* **Smart Normalization:** Optional ignore/normalize rules for non-leading whitespace and blank lines.
* **Context-Aware:** Dynamically loads configuration from :file:`pyproject.toml` or user-defined files.
* **Safety First:** Built-in dry-run mode and flexible backup options (including timestamped suffixes).
* **Cross-Platform:** Consistent behavior on Linux, macOS, and Windows.

Installation
------------

Install the package via pip:

.. code-block:: bash

   pip install ftw-patch

Quick Start
-----------

Once installed, use the :command:`ftwpatch` command to apply a unified diff:

.. code-block:: bash

   ftwpatch my_changes.patch

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   user/use_ftwpatch

.. toctree::
   :maxdepth: 1
   :caption: Project Info:

   changelog
   license

.. toctree::
   :maxdepth: 1
   :caption: Developer Guides:

   devel/get_started_ftw_patch
   devel/ftw_patch_module


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

.. |cc-logo| image:: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
   :target: https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en
   :alt: CC BY-NC-SA 4.0


Licensed under |cc-logo|
`Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International 
<https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en>`_ [cite: 9, 10]

.. topic:: Citing this documentation

   Please cite this work as follows: 
   
   Fitzz TeXnik Welt. 
   (2025). *ftw-patch: A Unicode-resilient replacement for the classic patch tool* 
   (Version 1.0.0) [Software documentation]. Retrieved from https://github.com/fitzz-ftw/ftw-patch



   