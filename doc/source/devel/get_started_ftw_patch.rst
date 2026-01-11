.. role:: py:mod(strong)
.. role:: py:func(strong)
.. role:: py:meth(strong)
.. role:: py:class(strong)

.. _ftw-patch-intro:

Getting Started with Classes from Patch Module 
=================================================

:Author: Fitzz TeΧnik Welt
:Email: FitzzTeXnikWelt@t-online.de

This document provides a step-by-step introduction and executable documentation for the core logic in the ``fitzzftw.patch`` module.

.. seealso:: The full API documentation for the module is available here: :py:mod:`fitzzftw.patch.ftw_patch`

---

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
        >>> env.do_not_clean = True



Class PatchLine 
----------------


.. code:: python 

    >>> from fitzzftw.patch.ftw_patch import PatchLine

    >>> patchline = PatchLine("This is a test line.\n")
    >>> patchline
    PatchLine(Content: 'This is a test line.')

    >>> print(patchline)
    PatchLine(Content: 'This is a test line.')

    >>> patchline.content
    'This is a test line.'

    >>> patchline.has_trailing_whitespace
    False

    >>> PatchLine("This is a test line.  \n").has_trailing_whitespace
    True

    >>> patchline_ws = PatchLine("This is a test line.\n   ")
    >>> patchline_ws.has_trailing_whitespace
    True

    >>> patchline_ws
    PatchLine(Content: 'This is a test line.\n   ')

    >>> patchline_ws.content
    'This is a test line.\n   '


Class FileLine 
---------------

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import FileLine

    >>> fileline = FileLine("  def func( a,    b):   \n")
    >>> fileline 
    FileLine(Content: '  def func( a,    b):   ', Prefix: '')

    >>> fileline.content
    '  def func( a,    b):   '

    >>> fileline.prefix
    ''

    >>> fileline.normalized_ws_content
    '  def func( a, b):'

    >>> fileline.ignore_all_ws_content
    'deffunc(a,b):'

    >>> fileline.has_newline
    True


    >>> fileline.line_string
    '  def func( a,    b):   \n'

    >>> fileline_nl = FileLine("    return True")
    >>> fileline_nl.has_newline
    False

    >>> fileline_nl.line_string
    '    return True'


    >>> fileline.has_trailing_whitespace
    True


    >>> FileLine("def test(self):").has_newline
    False

FileLine Class
--------------------
.. _ftw_patch-fileline-class:

:Inherits: :py:class:`PatchLine`
:Purpose: Represents a single line within a code file.

The :py:class:`fitzzftw.patch.ftw_patch.FileLine` class represents a single line of text from a 
file. Its core function is to immediately **strip the trailing newline character** from 
the input and provide the clean, ready-to-use content via the :py:attr:`content` property.

Initialization and Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. _ftw_patch-fileline-init-method:

The class is initialized solely with the raw line input as the **first positional argument**.

1. **Import the FileLine class and create a standard line**. The internal logic immediately strips the newline, exposing the clean content via the **``content``** property.

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import FileLine
    >>> line1 = FileLine("This is line 1.\n")
    >>> line1.content
    'This is line 1.'

2. **Create a line that lacks a trailing newline** (e.g., the last line of a file). In this case, `content` simply returns the input string, as no stripping is necessary.

.. code:: python

    >>> line2 = FileLine("Final line content")
    >>> line2.content
    'Final line content'

3. **Verify the output of the ``__repr__`` method**, which reflects the objects class name and state.

.. code:: python

    >>> line1 
    FileLine(Content: 'This is line 1.', Prefix: '')


Property: :py:attr:`is_empty`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. _ftw_patch-fileline-isempty-property:

This read-only property checks if the line contains an empty string (i.e., if ``content`` is empty). Note that a string containing 
only whitespace is not considered empty by this check.

.. code:: python

    >>> FileLine("").is_empty
    True
    >>> FileLine(" ").is_empty
    False
    >>> line1.is_empty
    False
    >>> FileLine("\n").is_empty
    True


Property: :py:attr:`normalized_ws_content`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. _ftw_patch-fileline-normalizedwscontent-property:

This property returns the line content with all internal whitespace sequences (tabs, multiple spaces) 
collapsed into a single space, while preserving leading whitespace. This crucial feature relies on the 
already stripped content from the :py:attr:`content` property.

1. **Test simple internal whitespace collapse** using mixed spaces and tabs. The input includes the newline character, which is stripped internally before processing.

.. code:: python

    >>> FileLine("Item  A\tItem B  \n").normalized_ws_content
    'Item A Item B'

2. **Verify the preservation of leading whitespace**, as it often contains the patch prefix ('-' or '+') or context spacing.

.. code:: python

    >>> FileLine("  \t  Leading WS\tRest\n").normalized_ws_content
    '  \t  Leading WS Rest'

3. **Ensure empty content remains empty** after normalization.

.. code:: python

    >>> FileLine("").normalized_ws_content
    ''



Test the FileLine's capability to strip ALL whitespace for the 'ignore-all-whitespace' mode.
 
The expected result is a string containing only non-whitespace characters.
 
1. Test case with leading/trailing spaces, tabs, and Non-Breaking Space (NBSP or '\xa0').

   All of these should be removed, leaving only the content string.

.. code:: python

    >>> line_with_all_ws = "\t  Item\xa0A\tItem B   \n"
    >>> FileLine(line_with_all_ws).ignore_all_ws_content
    'ItemAItemB'
    
1. Test case containing only whitespace characters (Standard Space, Tab, NBSP, Newline).

The expected result must be an empty string, confirming complete removal.
.. code:: python

    >>> FileLine("  \t\xa0 \n").ignore_all_ws_content
    ''



HunkLine Class
--------------

:Inherits: `PatchLine`
:Purpose: Represents a single content line within a hunk block of a unified diff.

The HunkLine class is implemented in the Patch Parser to encapsulate hunk line content and manage whitespace normalization.

.. code:: python

   >>> from fitzzftw.patch.ftw_patch import HunkLine

Initialization and Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test verifies the basic decomposition of the line into prefix and content.

.. code:: python

   >>> hl1 = HunkLine(" Content with spaces")
   >>> hl1.prefix
   ' '
   >>> hl1.content
   'Content with spaces'

Identifying a Context Line in a Parsed Hunk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:attr:`is_context` property identifies if a line is marked as context 
information within the patch. This allows for programmatic analysis of the 
patch content without manual string prefix checking **(ro)**.

.. code:: python

   >>> hl1.is_context
   True

.. _ftw_patch-hunk_line-is_deletion-property:

Identifying a Deletion Line in a Parsed Hunk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:attr:`is_deletion` property identifies if a line is marked for removal 
within the patch. This allows for programmatic analysis of the 
patch content without manual string prefix checking **(ro)**.

.. code:: python

    >>> hl1.is_deletion
    False

Identifying an Addition Line in a Parsed Hunk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:attr:`is_addition` property identifies if a line is marked as a new 
addition within the patch. This allows for programmatic analysis of the 
patch content without manual string prefix checking **(ro)**.

.. code:: python

    >>> hl1.is_addition
    False


Lines with Trailing Whitespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This test simulates a deletion line that includes trailing whitespace, 
which is important for the :py:attr:`has_trailing_whitespace` property.

.. code:: python

   >>> hl2 = HunkLine("-Remove this line. \t")
   >>> hl2.content
   'Remove this line. \t'
   >>> hl2.has_trailing_whitespace
   True

Error Handling (Missing Prefix)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The class must raise a :py:class:`PatchParseError` if 
the line does not have a valid diff prefix (' ', '+', '-').

.. code:: python

   >>> HunkLine("Missing prefix") # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
   Traceback (most recent call last):
   ...
   fitzzftw.patch.ftw_patch.PatchParseError: Hunk content line missing valid prefix 
   (' ', '+', '-') or is empty: 'Missing prefix'

Whitespace Normalization (Compare all 3 Properties)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test is critical and compares the three levels of dynamic whitespace 
handling (Default, --normalize-ws, --ignore-all-ws).

Original Content: Leading WS, Internal WS run, Trailing WS

.. code:: python

   >>> ws_raw = "+  def test_fn(  a, b ): \t"
   >>> hl_ws = HunkLine(ws_raw)

Default Content (Raw, only newline/prefix stripped)

.. code:: python

   >>> hl_ws.content
   '  def test_fn(  a, b ): \t'

Normalized WS (Internal collapses, trailing removed, leading kept)

.. code:: python

   >>> hl_ws.normalized_ws_content
   '  def test_fn( a, b ):'

.. code:: python

   >>> hl_ws2 = HunkLine("+  def    test_fn2(  \t   a, b ): \t")
   >>> hl_ws2.normalized_ws_content
   '  def test_fn2( a, b ):'


Ignore All WS (Removes all \s)

.. code:: python

   >>> hl_ws.ignore_all_ws_content
   'deftest_fn(a,b):'

Blank Line Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests an explicit blank context line (' '), which is important for the Blank 
Line Skip Logic.

.. code:: python

   >>> hl_blank = HunkLine(" ")
   >>> hl_blank.content
   ''
   >>> hl_blank.is_context
   True


HunkHeadLine Class
------------------
:Inherits: :py:class:`PatchLine`
:Purpose: Represents a hunk header line within a patch (starting with '@@ ').

Initialization and Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import HunkHeadLine
    >>> hhline1 = HunkHeadLine("@@ -1,2 +1,3 @@")
    >>> hhline1
    HunkHeadLine(Content: '-1,2 +1,3', Prefix: '@@ ')



.. code:: python

    >>> hhline1.prefix
    '@@ '

    >>> hhline1.old_start
    1

    >>> hhline1.old_len
    2

    >>> hhline1.new_start
    1

    >>> hhline1.new_len
    3

    >>> hhline1.coords
    (1, 2, 1, 3)

    >>> hhline1.content
    '-1,2 +1,3'

    >>> hhline1.info
    


    >>> hhline2 = HunkHeadLine("@@ -10,4 +10,6 @@ class DatabaseConnector:")
    >>> hhline2
    HunkHeadLine(Content: '-10,4 +10,6', Prefix: '@@ ')

.. dropdown:: Repeated Test for Properties, see above.
    :chevron: down-up
    :color: info

    .. code:: python
    
        >>> hhline2.prefix
        '@@ '

        >>> hhline2.old_start
        10

        >>> hhline2.old_len
        4

        >>> hhline2.new_start
        10

        >>> hhline2.new_len
        6

        >>> hhline2.coords
        (10, 4, 10, 6)

        >>> hhline2.content
        '-10,4 +10,6'

.. code:: python

    >>> hhline2.info
    ' class DatabaseConnector:'

Exception Handling
~~~~~~~~~~~~~~~~~~~

Invalid HunkHeadLine
^^^^^^^^^^^^^^^^^^^^^^^

The :py:class:`HunkHeadLine` class ensures that only valid unified diff headers 
are processed. It raises a ``ValueError`` if the required prefix is missing.

Raised when a :py:class:`HunkHeadLine` is initialized with a prefix other than '@@ '.

    >>> hhline_bad = HunkHeadLine("@ -10,4 +10,6 @@")
    Traceback (most recent call last):
     ...
    ValueError: Invalid HunkHeadLine: Expected '@@ ', got '@ -'

Invalid Hunk Coordinates
^^^^^^^^^^^^^^^^^^^^^^^^^

The parser also validates the numerical coordinates within the header to 
ensure they follow the unified diff specification. This prevents 
processing of malformed hunk information.

Raised when a :py:class:`HunkHeadLine` is initialized with incorrect coords.

    >>> hhline_bad = HunkHeadLine("@@ -10,4 +I0,6 @@")
    Traceback (most recent call last):
        ...
    ValueError: Invalid Hunk coordinates: '-10,4 +I0,6'




HeadLine Class
--------------
:Inherits: :py:class:`PatchLine`
:Purpose: Represents a file header line within a patch (starting with '--- ' or '+++ ')

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import HeadLine

Test Cases for staticmethode check_is_null_path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section documents the :py:meth:`check_is_null_path` staticmethode from 
:py:class:`HeadLine` class, which checks if a given path represents a 
**null path marker** (like `/dev/null` or `NUL`) used in patch 
files to signify file deletion or creation.


1. POSIX Null Path Check
^^^^^^^^^^^^^^^^^^^^^^^^

Test the standard POSIX null path marker. This check is **case-sensitive**.

The standard POSIX null path string

.. code:: python

    >>> HeadLine.check_is_null_path("/dev/null")
    True


Path object input

.. code:: python

    >>> HeadLine.check_is_null_path(Path("/dev/null"))
    True

POSIX path with incorrect casing (should fail)

.. code:: python

    >>> HeadLine.check_is_null_path("/dev/Null")
    False

2. Windows Null Path Check
^^^^^^^^^^^^^^^^^^^^^^^^^^

Test the Windows null path marker (`NUL`). This check is **case-insensitive**.

Standard Windows null path (Uppercase)

.. code:: python

    >>> HeadLine.check_is_null_path("NUL")
    True

Windows null path (Lowercase)

.. code:: python

    >>> HeadLine.check_is_null_path("nul")
    True

Windows null path (Mixed case)

.. code:: python

    >>> HeadLine.check_is_null_path("NuL")
    True

3. Invalid Paths and Types
^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure that invalid path strings and unexpected types 
(like :py:type:`None` or numbers) are correctly rejected 
and return :py:type:`False`.


A regular file path

.. code:: python

    >>> HeadLine.check_is_null_path("/etc/hosts")
    False

Empty string

.. code:: python

    >>> HeadLine.check_is_null_path("")
    False

Invalid type (:py:type:`None` Type), testing the robust handling

.. code:: python

    >>> HeadLine.check_is_null_path(None)
    False

Invalid type (:py:type:`Number`)

.. code:: python

    >>> HeadLine.check_is_null_path(123)
    False

---


Initialization and Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




    >>> hline1 = HeadLine("--- target/file.txt\n")
    >>> hline1
    HeadLine(Content: 'target/file.txt', Prefix: '--- ')

    >>> hline1.content
    'target/file.txt'

    >>> hline1.prefix
    '--- '

    >>> hline1.is_null_path
    False

    >>> hline1.is_orig
    True

    >>> hline1.is_new
    False

    >>> hline1.info

    >>> hline1.get_path(1).as_posix() 
    'file.txt'


    >>> hline2 = HeadLine("+++ b/src/new_module.py\t(metadata: created on 2025-12-21)\n")
    >>> hline2
    HeadLine(Content: 'b/src/new_module.py', Prefix: '+++ ')

    >>> hline2.content
    'b/src/new_module.py'

    >>> hline2.prefix
    '+++ '

    >>> hline2.is_null_path
    False

    >>> hline2.is_orig
    False

    >>> hline2.is_new
    True

    >>> hline2.info
    '(metadata: created on 2025-12-21)'

    >>> hline2.get_path(1).as_posix()
    'src/new_module.py'

    >>> HeadLine("--- /dev/null\n").is_null_path
    True

Exception: Strip level
~~~~~~~~~~~~~~~~~~~~~~

Raised when a strip level is equal or greater then the parts of the path.

.. code:: python

    >>> hline1.get_path(2) # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: Strip level -p2 is too high for 
    path 'target/file.txt' (only 2 segments available).






Hunk Class
----------
.. _ftw_patch-hunk-class:

The :py:class:`fitzzftw.patch.ftw_patch.Hunk` dataclass represents a single contiguous block of 
changes ("a hunk") within a file being patched. It primarily stores the line number 
and length metadata, as well as the content of the changes (the **hunk lines**).

Initialization and Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. _ftw_patch-hunk-init-method:

The dataclass is initialized with the key statistics derived from the 
**hunk header** and the list of :py:class:`FileLine` objects containing the 
actual changes.

1. **Import the Hunk class** 

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import Hunk

2. **Initialize a standard Hunk** that deletes 2 lines and adds 3 lines, 
   resulting in a net increase of 1 line. The newline metadata is also stored.

.. code:: python

    >>> hunk1 = Hunk(hhline1)
    >>> hunk1
    Hunk(header=(1, 2, 1, 3), lines=0)

Adding some :py:class:`HunkLine` 

.. code:: python

    >>> hunk1.add_line(HunkLine("-Old Line 1\n"))
    >>> hunk1.add_line(HunkLine("-Old Line 2\n"))
    >>> hunk1.add_line(HunkLine("+New Line A\n"))
    >>> hunk1.add_line(HunkLine("+New Line B\n"))
    >>> hunk1.add_line(HunkLine("+New Line C\n"))

    >>> hunk1
    Hunk(header=(1, 2, 1, 3), lines=5)


    
    >>> hunk1.old_start
    1
    
    >>> hunk1.new_start
    1

The size of of a :py:class:`Hunk` is defiend by it's :py:class:`HunkLines`. 

.. code:: python

    >>> len(hunk1)
    5

    >>> hunk1[2]
    HunkLine(Content: 'New Line A', Prefix: '+')

    >>> for line in hunk1:
    ...     line
    HunkLine(Content: 'Old Line 1', Prefix: '-')
    HunkLine(Content: 'Old Line 2', Prefix: '-')
    HunkLine(Content: 'New Line A', Prefix: '+')
    HunkLine(Content: 'New Line B', Prefix: '+')
    HunkLine(Content: 'New Line C', Prefix: '+')


The DiffCodeFile Class
----------------------

A :py:class:`DiffCodeFile` represents all changes within a single source file. 
It is typically created by the parser, but it can also be used independently. 
It stores header information and acts as a container for hunks.


Initialization and Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import DiffCodeFile

Manual initialization (as the parser would do it)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    >>> source = HeadLine("--- a/old_name.py\n")
    >>> target = HeadLine("+++ b/new_name.py\n")
    >>> diff_file = DiffCodeFile(source)

    >>> diff_file
    DiffCodeFile(orig=a/old_name.py, hunks=0)

    >>> diff_file.new_header = target

Attributes
^^^^^^^^^^^^^^^^^

.. code:: python

    >>> diff_file.orig_header
    HeadLine(Content: 'a/old_name.py', Prefix: '--- ')

    >>> diff_file.new_header
    HeadLine(Content: 'b/new_name.py', Prefix: '+++ ')



Container Protocols (empty state)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    >>> len(diff_file)
    0
    >>> list(diff_file)
    []

Adding Data
~~~~~~~~~~~~

.. code:: python

    >>> hunk = Hunk(hhline1)
    >>> diff_file.add_hunk(hunk)
    >>> len(diff_file)
    1

    >>> diff_file.add_hunk(Hunk(hhline2))
    >>> len(diff_file)
    2


Getting Lines with Index
~~~~~~~~~~~~~~~~~~~~~~~~~
.. code:: python

    >>> diff_file[0]
    Hunk(header=(1, 2, 1, 3), lines=0)


    >>> diff_file[1]
    Hunk(header=(10, 4, 10, 6), lines=0)

    >>> diff_file
    DiffCodeFile(orig=a/old_name.py, hunks=2)

    >>> for code_file in diff_file:
    ...     code_file
    Hunk(header=(1, 2, 1, 3), lines=0)
    Hunk(header=(10, 4, 10, 6), lines=0)

.. _ftw_patch-utilities-get_backup_extension-auto:

:py:func:`get_backup_extension`
---------------------------------------------------

Import ``get_backup_extension``

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import get_backup_extension

The following tests demonstrate the sanitization and keyword resolution.

Standard normalization

.. code:: python

    >>> get_backup_extension("  .bak  ")
    '.bak'

For convenience, the keyword ``auto`` is supported alongside ``date``, 
``time``, and ``datetime``. All these keywords generate a full 
timestamped suffix for unique backup identification.


Using 'auto' for timestamped backups

.. code:: python

    >>> get_backup_extension("auto") # doctest: +ELLIPSIS
    '.bak_20...'

Maleformed extention string

.. code:: python

    >>> get_backup_extension(" . auto . ") # doctest: +ELLIPSIS
    '.bak_20...'


Using 'time' for timestamped backups

.. code:: python

    >>> get_backup_extension("time") # doctest: +ELLIPSIS
    '.bak_20...'

Using 'date' for timestamped backups

.. code:: python

    >>> get_backup_extension("date") # doctest: +ELLIPSIS
    '.bak_20...'

Using 'datetime' for timestamped backups

.. code:: python

    >>> get_backup_extension("datetime") # doctest: +ELLIPSIS
    '.bak_20...'

.. _ftw_patch-utilities-get_backup_extension-timestamp:

The ``timestamp`` keyword
~~~~~~~~~~~~~~~~~~~~~~~~~

You can also use the explicit keyword ``timestamp`` to achieve the same 
ISO-compliant backup suffix.
Using 'timestamp' for timestamped backups

Using 'timestamp' as a clear technical alias

.. code:: python

    >>> get_backup_extension("timestamp") # doctest: +ELLIPSIS
    '.bak_20...'

Get the Configuration
^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    >>> user_config = env.copy2config("fitzzftw", "patch_config.toml", "patch.toml")


    >>> from fitzzftw.patch.ftw_patch import get_merged_config
    >>> get_merged_config("fitzzftw")
    {'backup': True, 'backupext': '.my_bak', 'normalize-ws': False}

    >>> pyproject = env.copy2cwd("test_pyproject.toml", "pyproject.toml")
    
    >>> get_merged_config("fitzzftw") # doctest: +NORMALIZE_WHITESPACE
    {'backup': True, 'backupext': 'timestamp', 
    'normalize-ws': False, 'dry-run': True, 
    'strip': 1}




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

    >>> try:
    ...     parser.parse_args(["--dry-run", "patch.diff"]) 
    ... except Exception as e:
    ...     print(e)
    argument --dry-run: invalid str2bool value: 'patch.diff'




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







---






PatchParser Class
-------------------

The :py:class:`fitzzftw.patch.ftw_patch.PatchParser` class is responsible for processing the patch file. It reads the patch format (typically Unified Diff) and divides it into logical units (the file data tuples).

.. code:: python

    >>> from fitzzftw.patch.ftw_patch import PatchParser, FtwPatchError


Line Classification with the PatchParser Factory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:meth:`PatchParser.create_line` staticmethod acts as a central factory. 
It analyzes the prefix of a raw string to determine its semantic role within a 
patch. Instead of working with plain text, the parser converts each line into a 
specialized object (such as :py:class:`HeadLine` or :py:class:`HunkHeadLine`).

This approach ensures that the specific logic for headers, coordinates, and code 
changes is encapsulated within the correct class. If a line does not match any 
known pattern, the factory provides a generic PatchLine as a fallback.

The following examples demonstrate how different prefixes trigger the creation of 
specific objects:

A file header starts with `'---'` or `'+++'`


.. code:: python

    >>> PatchParser.create_line("--- a/old.py")
    HeadLine(Content: 'a/old.py', Prefix: '--- ')

Hunk headers start with `'@@ '`

.. code:: python

    >>> PatchParser.create_line("@@ -1,2 +1,3 @@")
    HunkHeadLine(Content: '-1,2 +1,3', Prefix: '@@ ')

Content lines start with `'+'`, `'-'`, or `' '` (a space)

.. code:: python

    >>> PatchParser.create_line("+new_code()")
    HunkLine(Content: 'new_code()', Prefix: '+')

Unknown lines fall back to a generic :py:class:`PatchLine`

.. code:: python

    >>> PatchParser.create_line("Index: manifest.txt")
    PatchLine(Content: 'Index: manifest.txt')




Streaming Line Transformation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:meth:`PatchParser.get_lines` classmethod is a generator that processes an entire stream 
of text. It iterates through the input line by line, strips trailing newlines, and 
uses the factory to yield specialized objects. 

This streaming approach allows the parser to handle very large patches efficiently 
without loading the entire file into memory.

.. code:: python

    >> raw_input = [
    ...     "--- a/file.py",
    ...     "@@ -1,1 +1,1 @@",
    ...     "+new line"
    ...
    >>> _ = env.copy2cwd("simple.diff")
    >>> teststream=Path("simple.diff").open('r').readlines()
    
    >> test

    >>> lines = list(PatchParser.get_lines(teststream))
    >>> lines[0]
    HeadLine(Content: 'a/file.py', Prefix: '--- ')
    >>> lines[1]
    HunkHeadLine(Content: '-1,1 +1,1', Prefix: '@@ ')
    >>> lines[2]
    HunkLine(Content: 'new line', Prefix: '+')


Initialization 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Initialize the Parser

.. code:: python

    >>> patch_parser = PatchParser()
    >>> patch_parser # doctest: +ELLIPSIS
    PatchParser()


High-Level File Iteration
~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:meth:`iter_files` method is the primary entry point for processing complete 
patch sets. It implements a high-speed state machine that assembles raw lines into 
structured objects: :py:class:`DiffCodeFile`, :py:class:`Hunk`, and specialized 
:py:class:`PatchLine` types.

The parser is strict: it ensures that headers, hunks, and content lines appear 
in the correct logical order. If the sequence is corrupted, it raises an 
:py:class:`FtwPatchError`.

.. code:: python

    >>> patch_data = [
    ...     "--- a/test.py\n",
    ...     "+++ b/test.py\n",
    ...     "@@ -1,1 +1,1 @@\n",
    ...     " print('Hello World')\n"
    ... ]

    >>> files = list(patch_parser.iter_files(patch_data))

    >>> len(files)
    1
    >>> files[0]
    DiffCodeFile(orig=a/test.py, hunks=1)


Validation and Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The parser monitors the state of the diff and prevents invalid structures, 
such as content lines appearing before a hunk header or missing file headers.

Missing `'---'` header before `'@@ '`

.. code:: python

    >>> broken_patch = ["@@ -1,1 +1,1 @@\\n", " content\\n"]
    >>> list(patch_parser.iter_files(broken_patch))
    Traceback (most recent call last):
        ...
    fitzzftw.patch.ftw_patch.PatchParseError: Line 1: Found '@@ ' before file headers


Processing Complex Patches
~~~~~~~~~~~~~~~~~~~~~~~~~~

In real-world scenarios, a single patch often contains changes for multiple files, and each file may contain several hunks. The ``PatchParser`` handles these transitions automatically.

The following example demonstrates a stream containing two different files:

.. code:: python

    >>> complex_patch = [
    ...     "--- a/config.py\n", 
    ...     "+++ b/config.py\n",
    ...     "@@ -1,1 +1,2 @@\n", 
    ...     "-DEBUG = False\n", 
    ...     "+DEBUG = True\n",
    ...     "@@ -10,1 +12,1 @@\n", 
    ...     "  VERSION = '1.0'\n",
    ...     "--- a/main.py\n", 
    ...     "+++ b/main.py\n",
    ...     "@@ -5,1 +5,1 @@\n", 
    ...     "-print('start')\n", 
    ...     "+print('running')\n"
    ... ]
    >>> parser = PatchParser()
    >>> files = list(parser.iter_files(complex_patch))
    
Verify the first file and its two hunks

.. code:: python

    >>> config_file = files[0]
    >>> config_file
    DiffCodeFile(orig=a/config.py, hunks=2)

    >>> len(config_file)
    2

    >>> config_file.hunks # doctest: +NORMALIZE_WHITESPACE
    [Hunk(header=(1, 1, 1, 2), lines=2), 
     Hunk(header=(10, 1, 12, 1), lines=1)]

    >>> len(config_file.hunks[0])
    2

    >>> config_file.hunks[0].lines # doctest: +NORMALIZE_WHITESPACE
    [HunkLine(Content: 'DEBUG = False', Prefix: '-'), 
     HunkLine(Content: 'DEBUG = True', Prefix: '+')]

Verify the second file

.. code:: python

    >>> main_file = files[1]
    >>> main_file
    DiffCodeFile(orig=a/main.py, hunks=1)

    >>> len(main_file)
    1

    >>> main_file.hunks
    [Hunk(header=(5, 1, 5, 1), lines=2)]

    >>> len(main_file.hunks[0])
    2

    >>> main_file.hunks[0].lines # doctest: +NORMALIZE_WHITESPACE
    [HunkLine(Content: "print('start')", Prefix: '-'), 
     HunkLine(Content: "print('running')", Prefix: '+')]


Robustness: Empty Streams
~~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:class:`PatchParser` is designed to handle empty input streams without 
raising errors. If the provided iterable is empty, the generator simply 
terminates, yielding no objects. This behavior is crucial for processing 
potentially empty patch files or filtered streams.

.. code:: python

    >>> empty_stream = []
    >>> list(parser.iter_files(empty_stream))
    []


FtwPatch Class
-----------------------------

The :py:class:`fitzzftw.patch.ftw_patch.FtwPatch` class is the high-level controller 
of the module. It coordinates the parsing of the patch file and the application 
of changes to the target directory using a safe staging mechanism.

Initialization and Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. code:: python

    >>> from fitzzftw.patch.ftw_patch import FtwPatch
    >>> from argparse import Namespace



1. Preparation and Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To initialize the patcher, we provide an ``options`` object (:py:class:`Namespace`) 
containing all necessary settings.



We use the dummy_patch_file created in the setup
.. code:: python

    >>> Path("patch.diff").touch()
    >>> options = Namespace(
    ...     patch_file=Path("patch.diff"),
    ...     target_directory=Path("."),
    ...     strip_count=0,
    ...     normalize_whitespace=False,
    ...     ignore_blank_lines=False,
    ...     ignore_all_whitespace=False,
    ...     dry_run=False,
    ...     verbose=0
    ... )
    >>> patcher = FtwPatch(options)
    >>> patcher # doctest: +ELLIPSIS
    FtwPatch(patch_file=...('patch.diff'))

2. Executing the Patch (:py:class:`apply` method)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :py:meth:`apply` method executes the patching logic. It returns ``0`` 
if the process was successful.

.. code:: python

    >>> # Using the options defined above
    >>> patcher.apply(options)

Verifying Dry-Run Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A key feature of :py:class:`FtwPatch` is the ability to simulate changes. 
When ``options.dry_run`` is set to ``True``, the internal staging area is 
prepared, but no changes are written back to the target files.

Create a test file

.. code:: python

    >>> test_file = env.copy2cwd("hello.py")

    >> test_file = Path("hello.py")
    >> test_file.write_text("print('Old')\n")
    13
    
Define a patch for this file

.. code:: python

    >> patch_data = [
    ...     "--- hello.py\n",
    ...     "+++ hello.py\n",
    ...     "@@ -1,1 +1,1 @@\n",
    ...     "-print('Old')\n",
    ...     "+print('New')\n"
    ... ]
    >> Path("test.patch").write_text("".join(patch_data))
    70
    
    >>> _ =env.copy2cwd("hello.patch", "test.patch")

Set up dry_run

.. code:: python

    >>> options.patch_file = Path("test.patch")
    >>> options.dry_run = True
    >>> simulation = FtwPatch(options)
    >>> simulation.apply(options)
    
    
The file remains unchanged

.. code:: python

    >>> test_file.read_text()
    "print('Old')\n"




Inspecting Patcher Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once initialized, the :py:class:`FtwPatch` instance provides read-only 
access to its configuration and the results of the parsing process 
through various properties.

Basic paths used by the patcher:

Accessing the core paths

.. code:: python

    >>> patcher.patch_file_path.name
    'test.patch'
    >>> patcher.target_directory.as_posix()
    '.'

.. _ftw_patch-ftw_patch-strip_count-property:

:py:attr:`strip_count`
^^^^^^^^^^^^^^^^^^^^^^

The :py:attr:`strip_count` property returns the number of leading path components 
that are stripped from the file names found in the patch file **(ro)**.

Accessing the strip count configuration

.. code:: python

    >>> patcher.strip_count
    0

The patcher also exposes the normalization settings derived from the options:

.. code:: python

    >>> patcher.normalize_whitespace
    False
    >>> patcher.ignore_blank_lines
    False
    >>> patcher.ignore_all_whitespace
    False




Accessing Parsed Data
~~~~~~~~~~~~~~~~~~~~~~~~

The :py:attr:`parsed_files` property provides access to the structured data 
before or after the patch is applied. This is useful for generating 
reports or verifying the patch content programmatically.

In our previous setup, we used a patch with one file: 'hello.py'


.. code:: python

    >>> len(simulation.parsed_files)
    1
    >>> diff_file = simulation.parsed_files[0]
    >>> diff_file.orig_header.content
    'hello.py'
    >>> len(diff_file.hunks)
    1

Verbosity and Logging
~~~~~~~~~~~~~~~~~~~~~~~~

The verbosity level determines how much information is printed to the 
console during the execution of the :py:meth:`apply` method.

.. code:: python

    >>> patcher.verbose
    0

Inspecting the Patcher
~~~~~~~~~~~~~~~~~~~~~~

You can check the current configuration of an :py:class:`FtwPatch` instance through 
its read-only properties **(ro)**.

Check the configuration via properties

.. code:: python

    >>> patcher = FtwPatch(options)
    >>> patcher.dry_run
    True
    >>> patcher.verbose
    0

Verify paths are handled correctly

.. code:: python

    >>> isinstance(patcher.patch_file_path, Path)
    True

Advanced Configuration
~~~~~~~~~~~~~~~~~~~~~~

The patcher can handle different whitespace styles. This is useful when 
dealing with files from different operating systems. Enabling these 
options changes how the patch is parsed.

Enable whitespace normalization

.. code:: python

    >>> options.normalize_whitespace = True
    >>> advanced_patcher = FtwPatch(options)

The patcher now uses advanced parsing logic

.. code:: python

    >>> advanced_patcher.apply(options)

Simulation vs. Real Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:meth:`apply` method is a procedure that performs the patching process. 
You can switch between a safe simulation and the actual write process.


1. Simulation Mode (Safety first)

.. code:: python

    >>> options.dry_run = True
    >>> simulation = FtwPatch(options)
    >>> simulation.apply(options)

2. Real Application (Default behavior)

.. code:: python

    >>> options.dry_run = False
    >>> real_patcher = FtwPatch(options)

This executes the final commit to the file system

.. code:: python

    >>> real_patcher.apply(options)


.. _ftw_patch-ftw_patch-apply-backup_logic:

:py:meth:`ftw_patch.ftw_patch.FtwPatch.apply`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When applying changes, the patcher automatically creates backups of the 
modified files. If no specific backup directory is provided, the backup 
is created in the same directory as the original file using an extension.

.. code:: python

    >>> options.backup_ext = '.bak'
    >>> options.backup=True
    >>> options # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    Namespace(patch_file=...Path('test.patch'), 
        target_directory=...Path('.'), 
        strip_count=0, 
        normalize_whitespace=True, 
        ignore_blank_lines=False, 
        ignore_all_whitespace=False, 
        dry_run=False, 
        verbose=0, 
        backup_ext='.bak',
        backup=True)
    
.. code:: python

    >>> Path('hello.py').read_text()
    "print('New')\n"

Handling Patch Failures (Safety First)
--------------------------------------

A key feature of :py:class:`FtwPatch` is its integrity check. If the context of a 
patch (a "hunk") does not exactly match the target file, the process 
aborts immediately. 

This prevents the tool from applying changes to the wrong lines, ensuring 
your source code remains consistent.    

.. code:: python

    >>> patcher.apply(options) # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    Traceback (most recent call last):
        ...
    fitzzftw.patch.ftw_patch.PatchParseError: Hunk mismatch at line 1. 
    ... not match the hunk's context.

Verification of Atomicity
~~~~~~~~~~~~~~~~~~~~~~~~~

Because the patch failed the integrity check, no changes were written to 
the disk, and no backup file was created. The operation is atomic.

The backup should NOT exist because nothing was changed

.. code:: python

    >>> backup_file = Path("hello.py.bak")
    >>> backup_file.exists()
    False

The original file remains untouched

.. code:: python

    >>> orig_file = Path(patcher._patch_files[0].orig_header.content)
    >>> orig_file.read_text()
    "print('New')\n"


Error Handling
--------------

The :py:class:`FtwPatch` class ensures data integrity. If a patch is malformed 
or files are missing, it raises an exception to prevent partial changes.

Triggering an error with a missing file

.. code:: python

    >>> options.patch_file = Path("missing.patch")
    >>> FtwPatch(options).apply(options) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    FileNotFoundError: Patch file not found at ...Path('missing.patch')


Full Cycle: Patching a Python Source File
-----------------------------------------

To demonstrate the full power of :py:meth:`fitzzftw.patch`, we will perform a complete 
patching cycle: creating a source file, defining a unified diff, and applying it.

1. **Setup the Source File**
   We create a simple Python file with a few lines of code.

.. code:: python

    >>> source_path = env.copy2cwd("app.py")

2. **Create the Patch File**
   We define a patch that changes the greeting and adds a new function. 
   Notice the use of standard Unified Diff prefixes.

.. code:: python

    >>> patch_path = env.copy2cwd("changes.diff")

3. **Apply the Patch**
   Now we use ``FtwPatch`` to apply these changes. We will enable backup 
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
    >>> patcher.apply(run_options)


4. **Verify the Results**
   The original file should now contain the new content, and a backup 
   file ``app.py.orig`` should exist.

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

    >>> Path("app.py.orig").exists()
    True
    >>> "print('Hello')" in Path("app.py.orig").read_text()
    True



.. dropdown:: Before and After
    :chevron: down-up
    :color: info

    .. grid:: 2
        :gutter: 3

        .. grid-item-card:: Original Files (Input)
            :class-header: bg-light
            :shadow: md

            .. literalinclude:: testhome/testinput/app.py
                :language: python
                :linenos:
                :caption: app.py (original)

            .. literalinclude:: testhome/testinput/changes.diff
                :language: diff
                :caption: changes.diff

        .. grid-item-card:: Patched File (Output)
            :class-header: bg-success text-white
            :shadow: md

            .. literalinclude:: testhome/testoutput/app.py
                :language: python
                :linenos:
                :emphasize-lines: 2, 4-6
                :caption: app.py (patched)




.. dropdown:: Cleanup Testenvironment
    :chevron: down-up
    :color: info


    .. code:: python

        >>> env.input_readonly=False
        
        >>> env.teardown()
        
        >>> env.clean_home()
