Configuration Examples
======================

The keys in your TOML configuration files match the long-form names of the 
command-line arguments (e.g., use ``backupext`` for the 
:ftwpatchopt:`--backupext` option).

Project-specific (:file:`pyproject.toml`)
---------------------------------------------

Use this for settings that should be enforced for everyone working on this 
specific project.

.. code-block:: toml

   [tool.ftw.patch]
   backup = true
   backupext = ".original"
   normalize-ws = true

User-specific (:file:`patch.toml`)
--------------------------------------

Use this for your personal preferences across all your work where no 
project-specific :file:`pyproject.toml` is present.

.. code-block:: toml

   # Always use a specific backup extension and verbosity
   verbose = 1
   backupext = "datetime"
   
.. note::
   If you use the :ftwpatchopt:`--userconfig` flag, the path is resolved 
   relative to your CWD. 
   Example: ``ftwpatch --userconfig ./my_rules.toml <patch_file>`` will look 
   for the config exactly in your current folder.
