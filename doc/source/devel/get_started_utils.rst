Getting Started: Utilities
==========================

The :mod:`.utils` module provides helper functions for configuration and 
filesystem tasks. It ensures that the framework behaves consistently across 
different platforms.

Configuration Merging
---------------------

The framework uses a hierarchical configuration system. Settings are merged 
from multiple sources, where project-level files override user-level defaults.

We use :func:`~platformdirs:platformdirs.user_config_path` to find the 
correct location for settings on Linux, macOS, and Windows.

Example of configuration merging:

    >>> from fitzzftw.patch.utils import get_merged_config
    >>> # Returns a dict with merged settings from pyproject.toml and user config
    >>> config = get_merged_config(app_name="ftw")
    >>> isinstance(config, dict)
    True

Backup Extensions
-----------------

When modifying files, the framework can create backups. The utility function 
:func:`.utils.get_backup_extension` handles the naming logic.

If you use the 'timestamp' keyword, it generates an ISO-compliant suffix:

    >>> from fitzzftw.patch.utils import get_backup_extension
    >>> ext = get_backup_extension("timestamp")
    >>> ext.startswith(".bak_20")  # Check for current century
    True
    
You can also use simple extensions:

    >>> get_backup_extension(".old")
    '.old'
    >>> get_backup_extension("orig ")
    '.orig'
