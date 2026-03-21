.. SECTION - SetUp

.. _ftw-patch-setup-env:


.. dropdown:: Environment Setup and Path Initialization for the Tests
    :chevron: down-up
    :color: info

    .. code:: python

        >>> from pathlib import Path
        >>> from fitzzftw.develtool.testinfra import TestHomeEnvironment


        >>> env = TestHomeEnvironment(Path("doc/source/devel/testhome"))
        >>> env.setup()
        >>> env.input_readonly = True
        >>> env.do_not_clean = False

.. !SECTION

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import FtwPatch
    >>> from argparse import Namespace



1. **Setup the Source File**
   We create a simple Python file with a few lines of code.

.. code:: python
    >>> env.clean_home()
    >>> source_path = env.copy2cwd("app.py")
    >>> deleted_path = env.copy2cwd("app_old_config.py", "old_config.py")

2. **Create the Patch File**
   We define a patch that changes the greeting and adds a new function. 
   Notice the use of standard Unified Diff prefixes.

.. code:: python

    >>> patch_path = env.copy2cwd("changes_multi.diff","changes.diff")

.. "changes_multi.diff","changes_create.diff", "changes_delete.diff", "changes_multi_delete.diff"

3. **Apply the Patch**
   Now we use :class:`~.patcher.FtwPatch` to apply these changes. We will enable backup 
   generation to see the safety mechanism in action.

.. code:: python

    >>> from argparse import Namespace
    >>> run_options = Namespace(
    ...     patch_file=patch_path,
    ...     target_directory=Path("."),
    ...     strip_count=1,
    ...     normalize_whitespace=False,
    ...     ignore_blank_lines=False,
    ...     ignore_all_whitespace=False,
    ...     dry_run=False,
    ...     verbose=1,
    ...     backup=True,
    ...     backup_ext=".orig"
    ... )
    >>> patcher = FtwPatch(run_options)

    >>> env.input_readonly=False

    >>> patcher.apply(run_options)
    
    Traceback (most recent call last):
        ...
    fitzzftw.patch.exceptions.PatchParseError: Hunk starting at line 0 exceeds file bounds. File has 0 lines.

4. **Verify the Results**
   The original file should now contain the new content, and a backup 
   file :file:`app.py.orig` should exist.

.. code:: python

    >>> print(source_path.read_text())
    def greet():
        print('Hello World')
    <BLANKLINE>
    def farewell():
        print('Goodbye')
    <BLANKLINE>
    if __name__ == '__main__':
        greet()
    <BLANKLINE>

    >> Path("app.py.orig").exists()
    True
    >>> "print('Hello')" in Path("app.py.orig").read_text()
    True

    >>> Path("old_config.py.orig").exists()
    True

    >>> deleted_path.exists()
    False

    >>> Path("utils.py").exists()
    True

    >>> Path("utils.py.orig").exists()
    False






.. SECTION - CleanUp

.. dropdown:: Cleanup Testenvironment
    :chevron: down-up
    :color: info


    .. code:: python

        >>> env.input_readonly=False
        
        >>> env.do_not_clean = False

        >>> env.teardown()
        
        >> env.clean_home()

.. !SECTION
