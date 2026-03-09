"""
utils
===============================

| File: src/fitzzftw/patch/utils.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de
| License: LGPLv2 or above

Modul utils documentation
"""
from pathlib import Path
from tomllib import load as tomlload

from platformdirs import user_config_path


def get_backup_extension(ext: str) -> str:
    """
    Normalizes the backup extension and handles dynamic keywords.

    Input is cleaned by removing outer whitespace and dots. If a keyword is 
    detected, it is replaced by an ISO 8601 compliant timestamp.

    :param ext: The extension string or keyword ('date', 'time', 'datetime', 'auto', 'timestamp').
    :returns: A normalized string starting with a dot. Keywords result 
              in the format: '.bak_YYYY-MM-DDTHHMMSS'.
    """
    ext = ext.strip().strip(".").strip()
    
    # Aliases for the full ISO 8601 timestamp
    if ext in ('auto', 'date', 'time', 'datetime', 'timestamp'):
        import datetime
        ext = f"bak_{datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')}"
    
    return f".{ext}"

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

# Hier den Code einfügen

if __name__ == "__main__": # pragma: no cover
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
    test_file = testfiles_dir / "get_started_ftw_patch.rst"

    if test_file.exists():
        print("--- Running Doctest for utils ---")
        doctestresult = testfile(
            str(test_file),
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
