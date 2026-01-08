Changelog
=========
All notable changes to this project will be documented in this file.

v0.1.0 (2026-01-08)
-------------------

Initial Public Beta Release.

Added
~~~~~
* **Core Engine:** Robust patching logic with full Unicode support.
* **Normalization:** Added filters for non-leading whitespace and blank line variations.
* **Configuration:** Support for ``pyproject.toml`` [tool.ftwpatch] and custom ``.toml`` config files.
* **CLI:** Command-line tool ``ftwpatch`` with dry-run and backup functionality.
* **Documentation:** Complete user manual and developer guide.

Fixed
~~~~~
* Internal handling of mixed line endings during the patch process.
