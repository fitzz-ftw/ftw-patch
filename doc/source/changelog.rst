Changelog
=========
All notable changes to this project will be documented in this file.

.. rubric:: v0.5.0 (2026-04-02) Streaming Engine & Backup Directories
    :class: ftw-cr-title

.. rubric:: Added
    :class: ftw-cr-added

* **Streaming Parser:** Changed the internal engine to process files one by one. This shows progress immediately instead of waiting for the whole list.
* **Performance Tracking:** The final summary now shows the total runtime in seconds.
* **Dynamic Backup Directories:** Added the ``--backup-dir`` option. You can use keywords like ``@auto@`` or ``@datetime@`` to create timestamped folders.
* **Responsive Scroll Offsets:** Updated the CSS to handle fixed headers. Links now scroll to the correct position on all screen sizes.

.. rubric:: Fixed
    :class: ftw-cr-fixed

* **Property Logic:** Fixed the ``@property.setter`` syntax to prevent "missing argument" errors in IDEs.
* **Time Calculation:** Now uses ``total_seconds()`` to ensure correct time reports even for very long processes.
* **Exception Documentation:** Updated the hierarchy to list errors from specific to general in the documentation.

.. rubric:: Changed
    :class: ftw-cr-changed

* **Core Error Model:** ``FtwProtocolError`` now inherits from ``TypeError`` for better system integration.



.. rubric:: v0.4.0 (2026-03-26) Advanced Verbosity & Documentation Automation
    :class: ftw-cr-title

.. rubric:: Added
    :class: ftw-cr-added

* **Granular Verbosity Control:** Added support for verbosity levels 0–6 in ``PatchStatistics``, allowing users to toggle between silent operation and extreme debug-level detail.
* **Sphinx Documentation Suite:**
    * Integrated ``VerbosityTableDirective`` to automatically generate synchronized verbosity level tables from the source code.
    * Added ``:ftwoption:`` custom role for semantic linking and consistent styling of CLI parameters.
    * Implemented ``inject_option_anchors`` to provide automated HTML anchors for all configuration options.
* **Build Safety:** Introduced a ``guard-master`` check in the ``Makefile`` to prevent accidental direct pushes to protected branches.

.. rubric:: Fixed
    :class: ftw-cr-fixed

* **Windows Compatibility:** Forced POSIX-style forward slashes in ``PatchStatistics`` output by strictly using ``.as_posix()``, resolving string mismatch failures in doctests on Windows runners.
* **Documentation Layout:** Refined CSS for improved link visibility and better code block contrast in the HTML documentation.

.. rubric:: Changed
    :class: ftw-cr-changed

* **Output Refactoring:** Optimized the statistics engine to handle high-verbosity data collection without performance overhead in standard modes.


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


