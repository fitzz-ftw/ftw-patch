# File: src/fitzzftw/patch/utils.py
# Author: Fitzz TeXnik Welt
# Email: FitzzTeXnikWelt@t-online.de
# License: LGPLv2 or above

"""
General Utilities and Configuration Handling
============================================

This module provides helper functions for filesystem operations,
string normalization, and hierarchical configuration merging.

Core Functions:
---------------
* **get_string_of_type**:
    A robust helper to extract human-readable names from type objects or
    strings. It ensures consistent naming even when dealing with complex
    Protocols or edge cases where a simple `__name__` access might fail.
* **get_backup_extension**:
    Normalizes backup extensions and handles dynamic keywords like
    'timestamp' to generate ISO-compliant suffixes.
* **get_merged_config**:
    Implements the configuration layering logic, merging project-specific
    TOML files with global user preferences.

Key Features:
-------------
* **Configuration Priority**:
    Ensures that :file:`pyproject.toml` settings always override user-level
    defaults to maintain project standards.
* **Platform Awareness**:
    Uses :func:`platformdirs:platformdirs.user_config_path` to correctly resolve user
    configuration paths across different operating systems.
"""

from datetime import datetime
from pathlib import Path
from tomllib import load as tomlload

from platformdirs import user_config_path

DATETIME_KEYWORDS:set[str]=set(("auto", "date", "time", "datetime", "timestamp"))

# FUNCTION - get_string_of_type
def get_string_of_type(protocol_type) -> str:
    """
    Extracts a human-readable string representation of a type.

    This helper is used during protocol introspection to handle both actual
    class objects and pre-defined type strings. If the input has a '__name__'
    attribute (e.g., a class), it returns that name; otherwise, it returns
    the input as is.

    :param protocol_type: The type object or string to convert.
    :returns: A string representation of the type.
    """
    if hasattr(protocol_type, "__name__"):
        ret = protocol_type.__name__
    else:  # cov skip if >=3.14
        ret = protocol_type
        ret = str(ret)
    return ret
#!FUNCTION

# FUNCTION - replace_keywords_to_isodatetime
def replace_keywords_to_isodatetime(path_str:str, now:datetime)->str:
    """
    Replace predefined placeholders in a path string with an ISO timestamp.

    This function searches the string for tokens defined in DATETIME_KEYWORDS
    enclosed by '@' characters. It replaces them with a timestamp generated
    from 'now' using the format YYYYMMDDTHHMMSS.

    :param path_str: The path or filename string to process.
    :param now: The datetime.datetime object used as the source for the timestamp.
    :returns: The string containing the resolved timestamps.
    """
    ret:str=path_str
    ts_value:str = now.strftime("%Y%m%dT%H%M%S")
    for key in DATETIME_KEYWORDS:
        placeholder:str = f"@{key}@"
        if placeholder in ret:
            ret = ret.replace(placeholder, ts_value)
    return ret
# !FUNCTION - replace_keywords

# FUNCTION - get_backup_extension
def get_backup_extension(ext: str, now:datetime=datetime.now()) -> str:  # noqa: B008
    """
    Normalize the backup extension and handle dynamic keywords.

    This function cleans the input by removing outer whitespace and dots.
    If a keyword from DATETIME_KEYWORDS is detected, it is replaced by
    an ISO 8601 compliant timestamp.

    :param ext: The extension string or a valid datetime keyword.
    :param now: The datetime.datetime object used for timestamp generation.
    :returns: A normalized extension string starting with a dot and
        including the timestamp if a keyword was used.
    """
    ext = ext.strip().strip(".").strip()

    # Aliases for the full ISO 8601 timestamp
    if ext in DATETIME_KEYWORDS:
        ext = f"bak_{now.strftime('%Y-%m-%dT%H%M%S')}"

    return f".{ext}"
#!FUNCTION

# FUNCTION - get_merged_config
def get_merged_config(app_name: str = "ftw", manual_user_cfg: str = "") -> dict:
    """
    Merge configuration from hierarchical sources into a single dictionary.

    This function implements the configuration layering logic before the
    Pimple-object (args) is fully initialized. It resolves the 'chicken-and-egg'
    problem of locating the user configuration file via CLI before parsing
    the remaining arguments.

    The priority order for settings (highest to lowest):

    1. Project Configuration: Defined in 'pyproject.toml' under [tool.fitzzftw.patch].
       This level ensures project-specific standards (e.g., .gitignore compliance)
       always override global user preferences.
    2. Manual User Configuration: A TOML file specified via the '--userconfig' flag.
    3. Platform User Configuration: The default OS-specific path
       (e.g., ~/.config/ftw/patch.toml on Linux).

    :param app_name: The application namespace used for platformdirs resolution.
    :param manual_user_cfg: Optional filesystem path to a custom TOML config.
    :raises tomllib.TOMLDecodeError: If any encountered TOML file is syntactically invalid.
    :raises OSError: If there are permission issues accessing the configuration files.
    :returns: A dictionary containing the effective configuration defaults.
    """
    config = {}

    # 1. User level
    if manual_user_cfg:
        user_cfg_file = Path(manual_user_cfg)
    else:
        user_cfg_file = user_config_path(app_name) / "patch.toml"

    if user_cfg_file.exists():
        with open(user_cfg_file, "rb") as f:
            config.update(tomlload(f))

    # 2. Project level (always wins over user level)
    project_cfg_file = Path("pyproject.toml")
    if project_cfg_file.exists():
        with open(project_cfg_file, "rb") as f:
            data = tomlload(f)
            project_cfg = data.get("tool", {}).get(app_name, {}).get("patch", {})
            config.update(project_cfg)

    return config
#!FUNCTION


if __name__ == "__main__":  # pragma: no cover
    from doctest import FAIL_FAST, testfile
    from pathlib import Path

    be_verbose = False
    be_verbose = True
    option_flags = 0
    option_flags = FAIL_FAST
    test_sum = 0
    test_failed = 0

    # Pfad zu den dokumentierenden Tests
    testfiles_dir = Path(__file__).parents[3] / "doc/source/devel"
    test_file = testfiles_dir / "get_started_utils.rst"
    # test_file = testfiles_dir / "get_started_ftw_patch.rst"

    if test_file.exists():
        print("--- Running Doctest for utils ---")
        doctestresult = testfile(
            str(test_file),
            module_relative=False,
            verbose=be_verbose,
            optionflags=option_flags,
        )
        test_failed += doctestresult.failed
        test_sum += doctestresult.attempted
        if test_failed == 0:
            print(f"DocTests passed without errors, {test_sum} tests.")
        else:
            print(f"DocTests failed: {test_failed} tests.")
    else:
        print(f"⚠️ Warning: Test file {test_file.name} not found.")
