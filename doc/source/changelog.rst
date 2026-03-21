Changelog
=========
All notable changes to this project will be documented in this file.

.. rubric:: v0.3.2 (2026-03-20) Core Robustness & Statistics
    :class: ftw-cr-title

.. rubric:: Added
    :class: ftw-cr-added

* **Patch Statistics:** Introduced a metrics engine to track file operations (Created, 
  Modified, Deleted) and line-level changes (added/deleted lines) during the patch process.

.. rubric:: Fixed
    :class: ftw-cr-fixed

* **Null-Path Resolution:** Resolved a critical ``FileNotFoundError`` by strictly using the 
  ``is_null_path`` property to identify source or target "nothingness" (e.g., ``/dev/null``).
* **Staging Area Safety:** Improved temporary file creation to prevent the engine from 
  attempting to create OS-invalid paths during file creation or deletion.
* **Backup Logic:** The backup mechanism now intelligently skips non-existent files when a 
  patch creates a new file, preventing crashes in the pre-patch phase.

.. rubric:: v0.3.1 (2026-03-08) Documentation Overhaul
    :class: ftw-cr-title

.. rubric:: Added
    :class: ftw-cr-added

* **New Visual Identity:** Migrated to the *Nefertiti* theme for a modern, responsive HTML documentation.
* **Dynamic EPUB Covers:** Implemented automated generation of SVG covers that dynamically embed the current version from SCM.
* **Typography Enhancements:**
    * Integrated *Fira Sans* and *Fira Code* for better readability across all formats.
    * Added semantic roles for consistent styling of person names and configuration options.

.. rubric:: Changed
    :class: ftw-cr-changed

* **Build Optimization:** Improved EPUB build process by automatically filtering unnecessary font formats (WOFF2) to reduce file size.
* **Unified Versioning:** Versions are now automatically synchronized between the core engine and documentation.


.. rubric:: v0.3.0 (2026-01-11) Initial Public Release.
    :class: ftw-cr-title

.. rubric:: Added
    :class: ftw-cr-added

* **Core Engine:** Robust patching logic with full Unicode support.
* **Normalization:** Added filters for non-leading whitespace and blank line variations.
* **Configuration:** Support for ``pyproject.toml`` [tool.ftwpatch] and custom ``.toml`` config files.
* **CLI:** Command-line tool ``ftwpatch`` with dry-run and backup functionality.
* **CI/CD:** Automated testing and deployment infrastructure via GitHub Actions.
* **Documentation:** Complete user manual and developer guide.

.. rubric:: Fixed
    :class: ftw-cr-fixed

* Internal handling of mixed line endings during the patch process.


