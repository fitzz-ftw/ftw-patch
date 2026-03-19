Getting Started with Functions from Ftw-Patch Module 
======================================================


.. FUNCTION - _get_argparser

.. _ftw-patch-get-argparser-func:

:py:func:`_get_argparser` Function (Utility)
---------------------------------------------

This utility function parses the command-line arguments. We verify the defaults and argument parsing here.

First, import the necessary component:

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import _get_argparser 

For a full list of command-line options, refer to the :ref:`cli-reference`.

Initialize the parser:

.. code:: python

    >>> parser = _get_argparser()

Simulate passing the minimal required argument, the patch file path:

.. code:: python

    >>> args = parser.parse_args(["-p", "0","--dry-run","False","patch.diff"])

Verify default boolean options:

.. code:: python

    >>> args.dry_run
    False
    >>> args.verbose
    0

Verify integers and path settings:

.. code:: python

    >>> args.strip_count
    0

    >>> args.target_directory.as_posix()
    '.'

Verify the positional argument was mapped correctly:

.. code:: python

    >>> args.patch_file.name
    'patch.diff'

Verify FTW-specific normalization options default to **False**:

.. code:: python

    >>> args.normalize_whitespace
    False
    >>> args.ignore_blank_lines
    False
    >>> args.ignore_all_whitespace
    False

---

.. _ftw-patch-strip-count:

Handling Strip Count (:ftwpatchopt:`-p`)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test verifies that the :py:attr:`strip_count` argument is correctly parsed.

Test with the short option (:ftwpatchopt:`-p`) set to `3`:

.. code:: python

    >>> args_p = parser.parse_args(["-p", "3", "patch.diff"])
    >>> args_p.strip_count
    3

Test with the long option (:ftwpatchopt:`--strip`) set to `5`:

.. code:: python

    >>> args_strip = parser.parse_args(["--strip", "5", "patch.diff"])
    >>> args_strip.strip_count
    5

Test for non-numeric input, which should raise a `SystemExit` error:

.. code:: python

    >>> parser.parse_args(["-p", "a", "patch.diff"])
    Traceback (most recent call last):
        ...
    argparse.ArgumentError: argument -p/--strip: invalid int value: 'a'

    >>> parser.parse_args(["-h", "patch.diff"])
    Traceback (most recent call last):
        ...
    SystemExit: 0

---

.. _ftw-patch-dry-run:

Handling Dry Run (:ftwpatchopt:`--dry-run`)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test confirms that the boolean option :py:attr:`dry_run` is correctly set.

Test with the :ftwpatchopt:`--dry-run` option present:

Handling Ambiguous Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When using optional values with :py:attr:`nargs='?'`, positional arguments (like filenames) 
following a option might be mistaken for the option's value. Use the double-dash :ftwpatchopt:`--` 
to explicitly separate options from positional arguments.

This would fail, because "patch.diff" is not a boolean:

.. code:: python

    >>> parser.parse_args(["--dry-run", "patch.diff"])
    Traceback (most recent call last):
        ...
    argparse.ArgumentError: argument --dry-run: invalid str2bool value: 'patch.diff'



This succeeds:

.. code:: python

    >>> args = parser.parse_args(["--dry-run", "--", "patch.diff"])
    >>> args.dry_run
    True

.. code:: python

    >>> args_dry = parser.parse_args(["--dry-run", False, "patch.diff"])
    >>> args_dry.dry_run
    False

---

.. _ftw-patch-verbose:

Controlling Verbosity (:ftwpatchopt:`-v`)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test verifies that the verbosity level is correctly parsed and incremented.

Test with a single short option (:ftwpatchopt:`-v`):

.. code:: python

    >>> args_v1 = parser.parse_args(["-v", "patch.diff"])
    >>> args_v1.verbose
    1

Test with multiple short options (:ftwpatchopt:`-vvv`):

.. code:: python

    >>> args_v3 = parser.parse_args(["-vvv", "patch.diff"])
    >>> args_v3.verbose
    3

Test with the long option (:ftwpatchopt:`--verbose`):

.. code:: python

    >>> args_verbose = parser.parse_args(["--verbose", "patch.diff"])
    >>> args_verbose.verbose
    1

.. _ftw_patch-ftw_patch-backup-options:

Backup Extension Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :ftwpatchopt:`--backupext` option is flexible. It automatically ensures a leading 
dot is present and supports dynamic timestamps for automated workflows.

Example 1: Extension without a dot is normalized

.. code:: python

    >>> args = parser.parse_args(['--backup', '--backupext', 'orig', "test.diff"])

Your internal logic will handle the normalization to '.orig'

.. code:: python

    >>> args.backup_ext
    'orig'

Example 2: Using the 'time' keyword for a quick timestamp

.. code:: python

    >>> args = parser.parse_args(['--backup', '--backupext', 'time', "test.diff"])
    >>> args.backup_ext
    'time'


.. !FUNCTION

.. FUNCTION - prog_ftw_patch

Application Entry Point
-----------------------

The function :func:`.prog_ftw_patch` serves as the main entry point for 
the console script defined in ``pyproject.toml``.

It performs the following steps:
1. Initializes the argument parser via :func:`._get_argparser`.
2. Handles high-level exceptions (e.g., ``FtwPatchError``, ``TOMLDecodeError``).
3. Maps the parsed command-line arguments to the :class:`.FtwPatch` logic.

.. note::
   This function is designed to be called by the OS shell. For 
   programmatic use within other Python modules, it is recommended 
   to use the :class:`.patcher.FtwPatch` class directly.

.. !FUNCTION
