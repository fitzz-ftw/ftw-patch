:orphan:


Configuration
=============

``ftw-patch`` features a flexible, layered configuration system. This allows you to define global preferences while ensuring that project-specific requirements always take precedence.

Configuration Hierarchy
-----------------------

When you run ``ftwpatch``, settings are merged from several sources in a specific order. A setting from a higher-priority source will always override a setting from a lower-priority source.

**Priority Order (Highest to Lowest):**

1. **Command Line Arguments**
   Any flag passed directly in the terminal (e.g., ``--dry-run``) always has the final word.
   
2. **Project Configuration** (``pyproject.toml``)
   Settings defined in the ``[tool.ftw.patch]`` section of your project's root. This ensures, for example, that whitespace rules required by a specific project are always enforced.

3. **User Configuration** (``patch.toml``)
   Your personal defaults. By default, these are loaded from your OS-specific config directory:
   
   * **Linux:** ``~/.config/ftw/patch.toml``
   * **macOS:** ``~/Library/Application Support/ftw/patch.toml``
   * **Windows:** ``C:\Users\<User>\AppData\Local\ftw\patch.toml``

4. **Internal Defaults**
   If no configuration is found, the tool falls back to its built-in defaults (e.g., ``backup=False``, ``strip=0``).



The ``--userconfig`` Override
-----------------------------

You can bypass the standard User Configuration (Level 3) by providing a specific file via the CLI:

.. code-block:: bash

   ftwpatch --userconfig ./my-custom-settings.toml patch_file

.. note::
   The ``--userconfig`` flag is special: it is parsed before any other arguments to ensure the correct configuration is loaded to populate the help menu and default values. It cannot be set within a configuration file itself.

Configuration Format (TOML)
---------------------------

The keys in the TOML files correspond directly to the long-form CLI arguments. Boolean flags can be set to ``true`` or ``false``.

**Example** ``pyproject.toml``:

.. code-block:: toml

   [tool.ftw.patch]
   backup = true
   backupext = ".original"
   normalize-ws = true
   verbose = 1

**Example** ``patch.toml`` (User Config):

.. code-block:: toml

   # Global preference: always use verbose output
   verbose = 2
   dry-run = false
