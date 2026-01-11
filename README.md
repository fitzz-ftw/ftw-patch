## FTW Patch

**Author:** Fitzz TeXnik Welt

**Email:** FitzzTeXnikWelt@t-online.de

[![PyPI version](https://img.shields.io/pypi/v/ftw-patch.svg)](https://pypi.org/project/ftw-patch/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/ftw-patch.svg)](https://pypi.org/project/ftw-patch/)


[![PyPI version](https://img.shields.io/pypi/v/ftw-patch.svg)](https://pypi.org/project/ftw-patch/)
[![Documentation Status](https://readthedocs.org/projects/ftw-patch/badge/?version=latest)](https://ftw-patch.readthedocs.io/en/latest/?badge=latest)
[![Code Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://codecov.io/gh/fitzz-ftw/ftw-patch)
[![Doc Coverage](https://img.shields.io/badge/doc--coverage-100%25-brightgreen)](https://ftw-patch.readthedocs.io/)
[![Linting: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
[![Downloads](https://static.pepy.tech/badge/ftw-patch)](https://pepy.tech/project/ftw-patch)



### Abstract
A unicode-resistant replacement for the classic `patch` utility. This tool is designed to handle patches reliably, even when dealing with special characters or different file encodings that often cause issues with traditional tools.

---

## Installation

Install `ftw-patch` easily via pip:

```bash
pipx install ftw-patch
```

## Features

* **Unicode-Safe:** Reliable processing of files with special characters and various encodings.
* **Modern Python Support:** Fully tested and optimized for Python 3.11 up to the latest version 3.15.
* **Cross-Platform:** Works seamlessly on Linux, macOS, and Windows.
* **Configuration Support:** Settings can be pre-defined in `pyproject.toml` or a custom user TOML file.
* **Robust Path Handling:** Uses `platformdirs` to ensure clean and standard-compliant file paths.
* **High Quality:** Developed with high test coverage and verified via automated `tox` builds.
* **Advanced Whitespace Handling:** Options to normalize non-leading whitespace or ignore blank line differences.
* **Safety First:** Includes a `--dry-run` mode to simulate changes and automatic backup functionality.

## Usage (Command Line Interface)

`ftw-patch` is primarily used as a command-line tool.

### Basic Syntax
```bash
ftwpatch [options] patch_file
```

### Key Arguments & Options

* **`patch_file`**: The path to the unified diff or patch file.
* **`-h, --help`**: Show the help message and exit.
* **`-p, --strip <count>`**: Set the number of leading path components to strip from file names before trying to find the file (default: 0).
* **`-d, --directory <dir>`**: Change the working directory to `<dir>` before starting to look for files to patch.
* **`--normalize-ws`**: Normalize non-leading whitespace (replace spaces/tabs with a single space) in context and patch lines before comparison.
* **`--ignore-bl`**: Ignore differences in the number of consecutive blank lines.
* **`--ignore-all-ws`**: Ignore all whitespace (leading, non-leading, and blank lines). This overrides `--normalize-ws` and `--ignore-bl`.
* **`--dry-run`**: Simulate the process without writing any changes to the file system.
* **`-b, --backup`**: Create a backup of each file before applying patches.
* **`--backupext <ext>`**: Extension for backup files (default: `.bak`). Supports special keywords: `date`, `time`, or `datetime` for ISO 8601 timestamps.
* **`--userconfig <path>`**: Path to a custom user TOML configuration file.

> **Note:** Settings can also be loaded from `pyproject.toml` under `[tool.ftw.patch]`.


### Configuration via pyproject.toml

You can pre-configure `ftwpatch` in your project's `pyproject.toml` file. This is useful for setting permanent defaults for your project.

Add a section `[tool.ftw.patch]` like this:

```toml
[tool.ftw.patch]
backup = true
backupext = ".original"
normalize-ws = true
strip = 1
```

### User Configuration and User Config File

If you want to use `ftw-patch` with the same settings across multiple projects, you can create a central user configuration file. The tool automatically searches for a `patch.toml` file in your standard user configuration directory.

**Standard Locations:**
* **Linux:** `~/.config/ftw-patch/patch.toml`
* **macOS:** `~/Library/Application Support/ftw-patch/patch.toml`
* **Windows:** `%AppData%\ftw-patch\patch.toml`

**Example `patch.toml`:**
```toml
# Your personal defaults
backup = true
backupext = ".original"
normalize-ws = true
```

> **Note:** You can override these defaults at any time by using command-line options or a project-specific `pyproject.toml`. If you want to use a specific configuration file from a different location, use the `--userconfig <path>` option.



## Licensing

This project uses different licenses for software and documentation:

### Software (Code)
The source code of `ftw-patch` is licensed under the **GNU General Public License, Version 2**. 
This allows free use, modification, and integration, provided that the terms of the GPLv2 (such as distributing the source code when you share the software) are met.

### Documentation
The documentation (content in the `docs/` directory and manuals) is licensed under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**.
* **NC (Non-Commercial):** Commercial use of the documentation (e.g., selling it as a printed book) is prohibited without express permission.
* **BY / SA:** Attribution and sharing under the same conditions are required.
