.. role:: py:mod(strong)
.. role:: py:func(strong)
.. role:: py:meth(strong)
.. role:: py:class(strong)

.. _ftw-patch-intro:

ftw.patch: Getting Started with Patch Application
=================================================

:Author: Fitzz TeXnik Welt
:Email: FitzzTeXnikWelt@t-online.de

This document provides a step-by-step introduction and executable documentation for the core logic in the ``ftw.patch`` module.

.. seealso:: The full API documentation for the module is available here: :py:mod:`ftw.patch.ftw_patch`

---

.. _ftw-patch-setup-env:

..
    Environment Setup and Path Initialization
    -----------------------------------------



.. dropdown:: Environment Setup and Path Initialization for the Tests
    :chevron: down-up
    :color: info

    **Important Note for Users:** The following code blocks (Sections 1 through 3) are **only used to set up an isolated test environment** for the DocTests. These steps are required for the tests to run correctly and ensure test coverage. As an end-user or reader of the documentation, you **do not need to understand or run** this code; it is solely for information about the test conditions.


    The setup is divided into three separate DocTest blocks. Since these commands produce no output, they appear as compact executable lines in the rendered document.

    1. Module Imports

    .. code:: python
        
        >>> import os
        >>> import sys
        >>> from pathlib import Path


    2. Global Variable Definitions
    

    .. code:: python

        >>> TEST_BASEDIR = Path("doc/source/devel/testhome")
        >>> TEST_INPUT = TEST_BASEDIR / "testinput"
        >>> TEST_CWD = TEST_BASEDIR / "testoutput"


    3. File System and Environment Setup
    

    .. code:: python

        >>> TEST_BASEDIR.mkdir(parents=True, exist_ok=True)
        >>> os.environ['HOME'] = str(TEST_BASEDIR.resolve())
        >>> TEST_INPUT.mkdir(parents=True, exist_ok=True)
        >>> TEST_CWD.mkdir(parents=True, exist_ok=True)
        >>> CONFIG_DIR = TEST_BASEDIR / ".config/ftw"
        >>> CONFIG_DIR.mkdir(parents=True, exist_ok=True)


    Verification using path abstraction to ensure environment is set:

    .. code:: python

        >>> expected_suffix = 'doc/source/devel/testhome'
        >>> resolved_home = os.environ['HOME']
        >>> start_index = resolved_home.rfind(expected_suffix)
        >>> print(f"HOME set to: .../{resolved_home[start_index:]}") # doctest: +ELLIPSIS
        HOME set to: .../doc/source/devel/testhome
        >>> print(f"TEST_CWD (Write): {TEST_CWD.name}")
        TEST_CWD (Write): testoutput
        >>> os.chdir(TEST_CWD)


    ---

.. dropdown:: Temporary Patch File Setup
    :chevron: down-up
    :color: info
    
    We create a dummy patch file in the CWD (`TEST_CWD`) to allow the **FtwPatch class initialization** to succeed the file existence check.

    .. code:: python

        >>> dummy_patch_file = Path("patch.diff")
        >>> dummy_patch_file.touch()



    .. rubric:: Understanding the Current Working Directory (CWD)
    

    The variable **`TEST_CWD`** (`testoutput`) defines the isolated 
    location where files are created and patched. In the subsequent 
    tests, we intentionally switch the **Current Working Directory 
    (CWD)** to this path using `with Path(TEST_CWD).cwd():`. This 
    means all **relative paths** used within those test blocks 
    (like calling the patch on `./target/file.txt`) are relative 
    to `TEST_CWD`.

    ---



Class PatchLine 
================


.. code:: python 

    >>> from ftw.patch.ftw_patch import PatchLine

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
===============

.. code:: python

    >>> from ftw.patch.ftw_patch import FileLine

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

    >>> fileline.is_empty
    False

    >>> FileLine("\n").is_empty
    True

    >>> FileLine("").is_empty
    True

    >>> FileLine(" ").is_empty
    False

    >>> FileLine("def test(self):").has_newline
    False

FileLine Class
--------------------
.. _ftw_patch-fileline-class:

:Inherits: `PatchLine`
:Purpose: Represents a single line within a code file.

The :py:class:`ftw.patch.ftw_patch.FileLine` class represents a single line of text from a 
file. Its core function is to immediately **strip the trailing newline character** from 
the input and provide the clean, ready-to-use content via the **``content``** property.

Method: Initialization and Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. _ftw_patch-fileline-init-method:

The class is initialized solely with the raw line input as the **first positional argument**.

1. **Import the FileLine class and create a standard line**. The internal logic immediately strips the newline, exposing the clean content via the **``content``** property.

.. code:: python

    >>> from ftw.patch.ftw_patch import FileLine
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

    >>> line1 # doctest: +ELLIPSIS
    FileLine(...)


Property: is_empty
~~~~~~~~~~~~~~~~~~
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


Property: normalized_ws_content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. _ftw_patch-fileline-normalizedwscontent-property:

This property returns the line content with all internal whitespace sequences (tabs, multiple spaces) 
collapsed into a single space, while preserving leading whitespace. This crucial feature relies on the 
already stripped content from the ``content`` property.

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

   >>> from ftw.patch.ftw_patch import HunkLine

Test Case 1: Basic Initialization and Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test verifies the basic decomposition of the line into prefix and content.

.. code:: python

   >>> hl1 = HunkLine(" Content with spaces")
   >>> hl1.prefix
   ' '
   >>> hl1.content
   'Content with spaces'
   >>> hl1.is_context
   True

Test Case 2: Lines with Trailing Whitespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This test simulates a deletion line that includes trailing whitespace, which is important for the `has_trailing_whitespace` property.

.. code:: python

   >>> hl2 = HunkLine("-Remove this line. \t")
   >>> hl2.content
   'Remove this line. \t'
   >>> hl2.has_trailing_whitespace
   True

Test Case 3: Error Handling (Missing Prefix)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The class must raise a `PatchParseError` if the line does not have a valid diff prefix (' ', '+', '-').

.. code:: python

   >>> HunkLine("Missing prefix") # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
   Traceback (most recent call last):
   ...
   ftw.patch.ftw_patch.PatchParseError: Hunk content line missing valid prefix (' ', '+', '-') or is empty: 'Missing prefix'

Test Case 4: Whitespace Normalization (Compare all 3 Properties)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test is critical and compares the three levels of dynamic whitespace handling (Default, --normalize-ws, --ignore-all-ws).

Original Content: Leading WS, Internal WS run, Trailing WS
.. code:: python

   >>> ws_raw = "+  def test_fn(  a, b ): \t"
   >>> hl_ws = HunkLine(ws_raw)

Test 4a: Default Content (Raw, only newline/prefix stripped)
.. code:: python

   >>> hl_ws.content
   '  def test_fn(  a, b ): \t'

Test 4b: Normalized WS (Internal collapses, trailing removed, leading kept)
.. code:: python

   >>> hl_ws.normalized_ws_content
   '  def test_fn( a, b ):'

.. code:: python

   >>> hl_ws2 = HunkLine("+  def    test_fn2(  \t   a, b ): \t")
   >>> hl_ws2.normalized_ws_content
   '  def test_fn2( a, b ):'


Test 4c: Ignore All WS (Removes all \s)
.. code:: python

   >>> hl_ws.ignore_all_ws_content
   'deftest_fn(a,b):'

Test Case 5: Blank Line Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests an explicit blank context line (' '), which is important for the Blank Line Skip Logic.

.. code:: python

   >>> hl_blank = HunkLine(" ")
   >>> hl_blank.content
   ''
   >>> hl_blank.is_context
   True


HunkHeadLine Class
------------------
:Inherits: `PatchLine`
:Purpose: Represents a hunk header line within a patch (starting with '@@ ').

.. code:: python

    >>> from ftw.patch.ftw_patch import HunkHeadLine
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
    ''


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

Exception: Invalid HunkHeadLine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Raised when a `HunkHeadLine` is initialized with a prefix other than '@@ '.

    >>> hhline_bad = HunkHeadLine("@ -10,4 +10,6 @@")
    Traceback (most recent call last):
     ...
    ValueError: Invalid HunkHeadLine: Expected '@@ ', got '@ -'

Exception: Invalid Hunk coordinates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Raised when a `HunkHeadLine` is initialized with incorrect coords.

    >>> hhline_bad = HunkHeadLine("@@ -10,4 +I0,6 @@")
    Traceback (most recent call last):
        ...
    ValueError: Invalid Hunk coordinates: '-10,4 +I0,6'




HeadLine Class
--------------
:Inherits: `PatchLine`
:Purpose: Represents a file header line within a patch (starting with '--- ' or '+++ ')

.. code:: python

    >>> from ftw.patch.ftw_patch import HeadLine

Test Cases for staticmethode check_is_null_path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section documents the `check_is_null_path` staticmethode from HeadLine class, which checks 
if a given path represents a **null path marker** (like `/dev/null` or `NUL`) used in patch 
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

Ensure that invalid path strings and unexpected types (like `None` or numbers) are correctly rejected and return `False`.


A regular file path

.. code:: python

    >>> HeadLine.check_is_null_path("/etc/hosts")
    False

Empty string

.. code:: python

    >>> HeadLine.check_is_null_path("")
    False

Invalid type (NoneType), testing the robust handling

.. code:: python

    >>> HeadLine.check_is_null_path(None)
    False

Invalid type (Number)

.. code:: python

    >>> HeadLine.check_is_null_path(123)
    False

---


Test Cases for for Method and Properties
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

    >>> str(hline1.get_path(1)) # doctest: +ELLIPSIS
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

    >>> str(hline2.get_path(1))
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

The :py:class:`ftw.patch.ftw_patch.Hunk` dataclass represents a single contiguous block of 
changes ("a hunk") within a file being patched. It primarily stores the line number 
and length metadata, as well as the content of the changes (the **hunk lines**).

Method: Initialization and Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. _ftw_patch-hunk-init-method:

The dataclass is initialized with the key statistics derived from the **hunk header** and the list of :py:class:`FileLine` objects containing the actual changes.

1. **Import the Hunk class** 

.. code:: python

    >>> from ftw.patch.ftw_patch import Hunk

2. **Initialize a standard Hunk** that deletes 2 lines and adds 3 lines, resulting in a net increase of 1 line. The newline metadata is also stored.

.. code:: python

    >>> hunk1 = Hunk(hhline1)
    >>> hunk1
    Hunk(header=(1, 2, 1, 3), lines=0)

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
    
    >> len(hunk1)
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

A ``DiffCodeFile`` represents all changes within a single source file. It is typically created by the parser, but it can also be used independently. It stores header information and acts as a container for hunks.

.. code:: python

    >>> from ftw.patch.ftw_patch import DiffCodeFile

Manual initialization (as the parser would do it)

.. code:: python

    >>> source = HeadLine("--- a/old_name.py\n")
    >>> target = HeadLine("+++ b/new_name.py\n")
    >>> diff_file = DiffCodeFile(source)

    >>> diff_file
    DiffCodeFile(orig=a/old_name.py, hunks=0)

    >>> diff_file.new_header = target

1. Testing Attributes

.. code:: python

    >>> diff_file.orig_header
    HeadLine(Content: 'a/old_name.py', Prefix: '--- ')

    >>> diff_file.new_header
    HeadLine(Content: 'b/new_name.py', Prefix: '+++ ')


2. Testing Container Protocols (empty state)

.. code:: python

    >>> len(diff_file)
    0
    >>> list(diff_file)
    []

3. Adding Data

    >>> hunk = Hunk(hhline1)
    >>> diff_file.add_hunk(hunk)
    >>> len(diff_file)
    1

    >>> diff_file.add_hunk(Hunk(hhline2))
    >>> len(diff_file)
    2


4. Testing __getitem__

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

.. _ftw-patch-get-argparser-func:

_get_argparser() Function (Utility)
-----------------------------------

This utility function parses the command-line arguments. We verify the defaults and argument parsing here.

First, import the necessary component:

.. code:: python

    >>> from ftw.patch.ftw_patch import _get_argparser 

Initialize the parser:

.. code:: python

    >>> parser = _get_argparser()

Simulate passing the minimal required argument, the patch file path:

.. code:: python

    >>> args = parser.parse_args(["patch.diff"])

Verify default boolean flags:

.. code:: python

    >>> args.dry_run
    False
    >>> args.verbose
    0



Verify integers and path settings:

.. code:: python

    >>> args.strip_count
    0

    >>> str(args.target_directory)
    '.'

Verify the positional argument was mapped correctly:

.. code:: python

    >>> args.patch_file.name
    'patch.diff'

Verify FTW-specific normalization flags default to **False**:

.. code:: python

    >>> args.normalize_whitespace
    False
    >>> args.ignore_blank_lines
    False
    >>> args.ignore_all_whitespace
    False

---

.. _ftw-patch-strip-count:

Test Case 2: Handling Strip Count (-p)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test verifies that the `strip_count` argument is correctly parsed.

Test with the short flag (`-p`) set to `3`:

.. code:: python

    >>> args_p = parser.parse_args(["-p", "3", "patch.diff"])
    >>> args_p.strip_count
    3

Test with the long flag (`--strip`) set to `5`:

.. code:: python

    >>> args_strip = parser.parse_args(["--strip", "5", "patch.diff"])
    >>> args_strip.strip_count
    5

Test for non-numeric input, which should raise a `SystemExit` error:

.. code:: python

    >>> try: 
    ...     parser.parse_args(["-p", "a", "patch.diff"])
    ... except SystemExit as e:
    ...     print(f"SystemExit Code: {e.code}")
    SystemExit Code: 2

.. admonition:: Console Output Warning

    When this error case is executed, the :py:mod:`argparse` module outputs the error message and usage instruction to :py:data:`sys.stderr`.

    :warning: **Crucial Warning:** This :py:data:`sys.stderr` output often bypasses the test runner's standard capture (for both **doctest** and **pytest**). Consequently, the following output will appear directly in your terminal every time the test runs, even when it passes successfully:

    .. code::

        usage: ftwpatch [-h] [-p STRIP_COUNT] [-d TARGET_DIRECTORY] [--normalize-ws] [--ignore-bl] [--ignore-all-ws]
                        [--dry-run] [-v]
                        patch_file
        ftwpatch: error: argument -p/--strip: invalid int value: 'a'

---

.. _ftw-patch-dry-run:

Test Case 3: Handling Dry Run (--dry-run)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test confirms that the boolean flag `dry_run` is correctly set.

Test with the `--dry-run` flag present:

.. code:: python

    >>> args_dry = parser.parse_args(["--dry-run", "patch.diff"])
    >>> args_dry.dry_run
    True

---

.. _ftw-patch-verbose:

Test Case 4: Controlling Verbosity (-v)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This test verifies that the verbosity level is correctly parsed and incremented.

Test with a single short flag (`-v`):

.. code:: python

    >>> args_v1 = parser.parse_args(["-v", "patch.diff"])
    >>> args_v1.verbose
    1

Test with multiple short flags (`-vvv`):

.. code:: python

    >>> args_v3 = parser.parse_args(["-vvv", "patch.diff"])
    >>> args_v3.verbose
    3

Test with the long flag (`--verbose`):

.. code:: python

    >>> args_verbose = parser.parse_args(["--verbose", "patch.diff"])
    >>> args_verbose.verbose
    1

---

PatchParser Class
-------------------

The :py:class:`ftw.patch.ftw_patch.PatchParser` class is responsible for processing the patch file. It reads the patch format (typically Unified Diff) and divides it into logical units (the file data tuples).

.. code:: python

    >>> from ftw.patch.ftw_patch import PatchParser, FtwPatchError


Line Classification with the PatchParser Factory
-------------------------------------------------

The :py:meth:`PatchParser.create_line` staticmethod acts as a central factory. It analyzes the prefix of a raw string to determine its semantic role within a patch. Instead of working with plain text, the parser converts each line into a specialized object (such as HeadLine or HunkHeadLine).

This approach ensures that the specific logic for headers, coordinates, and code changes is encapsulated within the correct class. If a line does not match any known pattern, the factory provides a generic PatchLine as a fallback.

The following examples demonstrate how different prefixes trigger the creation of specific objects:

A file header starts with `'---'` or `'+++'`

.. code:: python

    >>> PatchParser.create_line("--- a/old.py")
    HeadLine(Content: 'a/old.py', Prefix: '--- ')

Hunk headers start with '@@'

.. code:: python

    >>> PatchParser.create_line("@@ -1,2 +1,3 @@")
    HunkHeadLine(Content: '-1,2 +1,3', Prefix: '@@ ')

Content lines start with '+', '-', or a space

.. code:: python

    >>> PatchParser.create_line("+new_code()")
    HunkLine(Content: 'new_code()', Prefix: '+')

Unknown lines fall back to a generic PatchLine

.. code:: python

    >>> PatchParser.create_line("Index: manifest.txt")
    PatchLine(Content: 'Index: manifest.txt')




Streaming Line Transformation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``PatchParser.get_lines`` method is a generator that processes an entire stream of text. It iterates through the input line by line, strips trailing newlines, and uses the factory to yield specialized objects. 

This streaming approach allows the parser to handle very large patches efficiently without loading the entire file into memory.

.. code:: python

    >>> raw_input = [
    ...     "--- a/file.py",
    ...     "@@ -1,1 +1,1 @@",
    ...     "+new line"
    ... ]
    >>> lines = list(PatchParser.get_lines(raw_input))
    >>> lines[0]
    HeadLine(Content: 'a/file.py', Prefix: '--- ')
    >>> lines[1]
    HunkHeadLine(Content: '-1,1 +1,1', Prefix: '@@ ')
    >>> lines[2]
    HunkLine(Content: 'new line', Prefix: '+')


Method: Initialization 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Initialize the Parser

.. code:: python

    >>> patch_parser = PatchParser()
    >>> patch_parser # doctest: +ELLIPSIS
    PatchParser()


High-Level File Iteration
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``iter_files`` method is the primary entry point for processing complete patch sets. It implements a high-speed state machine that assembles raw lines into structured objects: ``DiffCodeFile``, ``Hunk``, and specialized ``PatchLine`` types.

The parser is strict: it ensures that headers, hunks, and content lines appear in the correct logical order. If the sequence is corrupted, it raises an ``FtwPatchError``.

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

The parser monitors the state of the diff and prevents invalid structures, such as content lines appearing before a hunk header or missing file headers.

Missing '---' header before '@@'

.. code:: python

    >>> broken_patch = ["@@ -1,1 +1,1 @@\\n", " content\\n"]
    >>> list(patch_parser.iter_files(broken_patch))
    Traceback (most recent call last):
        ...
    ftw.patch.ftw_patch.FtwPatchError: Line 1: Found '@@' before file headers


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
    
    >>> # Verify the first file and its two hunks
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

    >>> # Verify the second file
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

The ``PatchParser`` is designed to handle empty input streams without raising errors. If the provided iterable is empty, the generator simply terminates, yielding no objects. This behavior is crucial for processing potentially empty patch files or filtered streams.

.. code:: python

    >>> empty_stream = []
    >>> list(parser.iter_files(empty_stream))
    []

