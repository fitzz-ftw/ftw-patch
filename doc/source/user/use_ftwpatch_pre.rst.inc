General Usage & Path Resolution
--------------------------------

Before exploring the individual command-line options, it is important to 
understand how the :command:`ftwpatch` command resolves paths and configuration files.

Strict Path Resolution
----------------------

To ensure maximum predictability and avoid "magic" behavior, :command:`ftwpatch`
follows strict rules:

* **Current Working Directory (CWD):** All relative paths (for patches, target 
  files, or config files) are resolved relative to the directory where you 
  execute the command.
* **Project Awareness:** The tool looks for a :file:`pyproject.toml` 
  **strictly** in the CWD. It does not search parent directories, ensuring 
  that settings from one project do not accidentally leak into another.

Configuration Priority
----------------------

Settings are merged from the following sources, where the higher level always overrides the lower ones:

1. **Command Line Arguments:** Explicit flags (e.g., :ftwpatchopt:`--dry-run`) always win.
2. **Project Configuration:** Settings in :file:`./pyproject.toml` under the ``[tool.ftw.patch]`` section.
3. **User Configuration:**

   * Either a manual file provided via the :ftwpatchopt:`--userconfig` option.
   * Or the default :file:`patch.toml` in your OS-specific config directory.

4. **Internal Defaults:** Built-in fallback values.

Dynamic Help & Defaults
-----------------------

A key feature of the :program:`ftwpatch` help system is that it is 
context-aware. The default values shown in the command-line help 
below are not hardcoded; they are recalculated every time you run 
the command.

When you call ``ftwpatch --help``, the tool first evaluates your 
:file:`pyproject.toml` and your user configuration. The "(default: ...)" 
strings in the output will reflect the **actually effective** values 
for your current environment. 

* If you change a setting in your :file:`pyproject.toml`, it will immediately 
  show up as the new default in your help output.
* If you use :ftwpatchopt:`--userconfig`, the help output will adapt to show the 
  values defined in that specific file.

Command Line Interface
----------------------

Below is the automatically generated help output for the :command:`ftwpatch` command:
