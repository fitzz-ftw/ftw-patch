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

Test Cases for is_null_path Function
------------------------------------

This section documents the `is_null_path` function, which checks if a given path represents a **null path marker** (like `/dev/null` or `NUL`) used in patch files to signify file deletion or creation.

.. code:: python

    >>> from ftw.patch.ftw_patch import is_null_path


1. POSIX Null Path Check
~~~~~~~~~~~~~~~~~~~~~~~~

Test the standard POSIX null path marker. This check is **case-sensitive**.

The standard POSIX null path string

.. code:: python

    >>> is_null_path("/dev/null")
    True

Path object input

.. code:: python

    >>> is_null_path(Path("/dev/null"))
    True

POSIX path with incorrect casing (should fail)

.. code:: python

    >>> is_null_path("/dev/Null")
    False

2. Windows Null Path Check
~~~~~~~~~~~~~~~~~~~~~~~~~~

Test the Windows null path marker (`NUL`). This check is **case-insensitive**.

Standard Windows null path (Uppercase)

.. code:: python

    >>> is_null_path("NUL")
    True

Windows null path (Lowercase)

.. code:: python

    >>> is_null_path("nul")
    True

Windows null path (Mixed case)

.. code:: python

    >>> is_null_path("NuL")
    True

3. Invalid Paths and Types
~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure that invalid path strings and unexpected types (like `None` or numbers) are correctly rejected and return `False`.


A regular file path

.. code:: python

    >>> is_null_path("/etc/hosts")
    False

Empty string

.. code:: python

    >>> is_null_path("")
    False

Invalid type (NoneType), testing the robust handling

.. code:: python

    >>> is_null_path(None)
    False

Invalid type (Number)

.. code:: python

    >>> is_null_path(123)
    False

---

FileLine Class
--------------------
.. _ftw_patch-fileline-class:

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




HunkLine
--------

The HunkLine class is implemented in the Patch Parser to encapsulate hunk line content and manage whitespace normalization.

.. code:: python

   >>> from ftw.patch.ftw_patch import HunkLine, PatchParseError

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

HunkContentData Named Tuple
----------------------------------
.. _ftw_patch-hunkcontentdata-namedtuple:

The :py:class:`ftw.patch.ftw_patch.HunkContentData` **Named Tuple** serves as a temporary container to store the parsed hunk information **before** it is compiled into the final :py:class:`Hunk` dataclass. It holds the raw list of lines as well as boolean flags that store the state of the line ending (**Newline**) for the original and new file content.

Attributes and Demonstration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Named Tuple is immutable and stores three main components: the parsed hunk lines and two boolean values indicating whether the last line of the original and new file content, respectively, ends with a newline character.

1.  **Import the Named Tuple** and the necessary :py:class:`FileLine` class.

.. code:: python

    >>> from ftw.patch.ftw_patch import HunkContentData, FileLine

2.  **Initialize a Named Tuple**. We store three lines (two context and one addition line) and set the flags for the newline status.

.. code:: python

    >>> lines = [FileLine(" Line 1\\n"), FileLine("+Added Line 2\\n"), FileLine(" Line 3\\n")]
    >>> content_data = HunkContentData(
    ...     lines=lines,
    ...     original_has_newline=True,
    ...     new_has_newline=False
    ... )
    >>> content_data.new_has_newline
    False

3.  **Verify Immutability and ``__repr__``** (Named tuples cannot be modified after creation).

.. code:: python

    >>> content_data # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    HunkContentData(lines=[FileLine(...), 
                    FileLine(...), ...], 
                    original_has_newline=True, 
                    new_has_newline=False)
    
    >>> try:
    ...     content_data.new_has_newline = True
    ... except AttributeError as e:
    ...     print(f"Error: {e}")
    Error: can't set attribute

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

1. **Import the Hunk dataclass** and the necessary :py:class:`FileLine` class.

.. code:: python

    >>> from ftw.patch.ftw_patch import Hunk, HunkLine

2. **Initialize a standard Hunk** that deletes 2 lines and adds 3 lines, resulting in a net increase of 1 line. The newline metadata is also stored.

.. code:: python

    >>> lines = [HunkLine("-Old Line 1\\n"), 
    ...          HunkLine("-Old Line 2\\n"), 
    ...          HunkLine("+New Line A\\n"), 
    ...          HunkLine("+New Line B\\n"), 
    ...          HunkLine("+New Line C\\n")]
    
    >>> hunk1 = Hunk(
    ...     original_start=10, 
    ...     original_length=2, 
    ...     new_start=10, 
    ...     new_length=3, 
    ...     lines=lines,
    ...     original_has_newline=True,
    ...     new_has_newline=True
    ... )
    
    >>> hunk1.original_start
    10
    
    >>> hunk1.new_length
    3
    
    >>> len(hunk1.lines)
    5

3. **Verify the output of the ``__repr__`` method**, which provides essential debugging information.

.. code:: python

    >>> hunk1 # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Hunk(original_start=10, original_length=2, 
        new_start=10, new_length=3, 
        lines=[HunkLine(...), HunkLine(...), ...], 
        original_has_newline=True, new_has_newline=True)


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

Verify default integers and path settings:

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
-----------------------------------------

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

Method: Initialization and ``iter_files``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. dropdown:: Setup and temporary patch file ..
    :chevron: down-up
    :color: info

    .. code:: python

        >>> import tempfile
        >>> from pathlib import Path
        
        >>> # 1. Create a temporary directory and a valid patch file
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> patch_content = """--- a/old_file.txt
        ... +++ b/new_file.txt
        ... @@ -1,2 +1,3 @@
        ...  Context Line 1
        ... -Deletion Line 2
        ... +Addition Line 2a
        ... +Addition Line 2b
        ...  Context Line 3
        ... """
        >>> patch_file = temp_dir / "test.patch"
        >>> with patch_file.open("w") as f:
        ...     _ = f.write(patch_content)

1. Initialize the Parser

.. code:: python

    >>> from ftw.patch.ftw_patch import PatchParser, FtwPatchError
    >>> patch_parser = PatchParser(patch_file)
    >>> patch_parser # doctest: +ELLIPSIS
    PatchParser(patch_file_path=PosixPath(...))

3. Iteration and Verification of the parsed data using ``iter_files()``.

.. code:: python

    >>> results = list(patch_parser.iter_files())
    >>> len(results)
    1
    >>> original_path, new_path, hunks = results[0]
    
Verification of the paths

.. code:: python

    >>> str(original_path)
    'a/old_file.txt'
    >>> str(new_path)
    'b/new_file.txt'

Verification of the Hunk content

.. code:: python
    
    >>> len(hunks)
    1
    >>> hunks[0].original_length
    2
    >>> hunks[0].new_length
    3
    >>> len(hunks[0].lines)
    5

.. note::
    The :py:meth:`~PatchParser.iter_files` method internally orchestrates the entire parsing process by calling several private methods which are implicitly tested here:

    * :py:meth:`~PatchParser._read_file_header` (to identify file paths).
    * :py:meth:`~PatchParser._read_hunk_header` (to identify hunk statistics).
    * :py:meth:`~PatchParser._read_hunk_content` (to parse :py:class:`FileLine` objects and newline metadata).
    * :py:meth:`~PatchParser._read_file` (utility method to consume and return the current line from the patch file).
    * :py:meth:`~PatchParser._peek_line` (utility method to look ahead at the next line without advancing the position).

Method: Error Handling
~~~~~~~~~~~~~~~~~~~~~~

.. dropdown:: Setup for invalid patch file ..
    :chevron: down-up
    :color: info

    .. code:: python

        >>> invalid_patch_content = """--- a/old_file.txt
        ... +++ b/new_file.txt
        ... -Deletion Line
        ... """
        >>> invalid_file = temp_dir / "invalid.patch"
        >>> with invalid_file.open("w") as f:
        ...     _ = f.write(invalid_patch_content)
        >>> invalid_parser = PatchParser(invalid_file)

2. Test the error handling (Missing Hunk Header). The iterator should raise an ``FtwPatchError``.

.. code:: python

    >>> try:
    ...     result = list(invalid_parser.iter_files())
    ... except FtwPatchError as e:
    ...     print(f"Expected Error: {e!s}")
    
    >>> len(result)
    0



.. _ftw-patch-class-init:

FtwPatch Class Initialization
-----------------------------

The :py:class:`ftw.patch.ftw_patch.FtwPatch` class encapsulates the patching logic.

First, import the class and its custom exception:

.. code:: python

    >>> from ftw.patch.ftw_patch import FtwPatch, FtwPatchError

Instantiate the class using the default `args` namespace object:

.. code:: python

    >>> args.dry_run
    False
    >>> ftw_app = FtwPatch(args=args)

Check if initialization correctly mapped the arguments:

.. code:: python

    >>> ftw_app.patch_file_path.name
    'patch.diff'
    >>> ftw_app.strip_count
    0
    >>> str(ftw_app.target_directory) 
    '.'

---

.. _ftw-patch-run-method:

FtwPatch.run() Method (Applying the Patch)
------------------------------------------

This section tests the core application of a patch file.

.. dropdown:: Setup for patching ...
    :chevron: down-up
    :color: info

    .. code-block:: python

        >>> target_dir = Path("target")
        >>> target_dir.mkdir(exist_ok=True)
        >>> target_file = target_dir / "file.txt"
        >>> target_file.write_text("Original content.\nSecond line.\n")
        31

        >>> patch_content = """--- target/file.txt
        ... +++ target/file.txt
        ... @@ -1,2 +1,2 @@
        ... -Original content.
        ... -Second line.
        ... +New content.
        ... +Third line added.
        ... """
        >>> patch_file_path = Path("../testinput/patch.diff")
        >>> patch_file_path.write_text(patch_content)
        122
        
        >>> print(target_file.read_text())
        Original content.
        Second line.
        <BLANKLINE>

The target file content before patching:

.. code:: python

    >>> target_file.read_text()
    'Original content.\nSecond line.\n'

Run Test Case 1: Default successful run (`verbose=0`). The current working directory (CWD) is temporarily changed to `TEST_CWD` for the patch application:

.. code:: python

    >>> args = parser.parse_args([str(patch_file_path.resolve())])
    >>> ftw_app = FtwPatch(args=args)
    >>> ftw_app.run()# doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Applying patch from ...Path(...patch.diff') in directory ...Path('.') 
    (strip=0, ws_norm=False, bl_ignore=False, all_ws_ignore=False).
    <BLANKLINE>
    --- Processing file: ...Path('target/file.txt') -> ...Path('target/file.txt') (1 hunks)
     - Applying Hunk 1/1 (@ Line 1: 2 -> 2)
     -> Patch successfully verified and stored in memory (2 lines).
    <BLANKLINE>
    Starting write/delete phase: Applying changes to file system...
     -> Successfully wrote ...Path('target/file.txt').
    <BLANKLINE>
    Successfully processed 1 file changes.
    0

Verify the patch application:

.. code:: python

    >>> target_file.read_text()
    'New content.\nThird line added.\n'

Run Test Case 2: Dry Run (Should not change content). First, revert the target file to its original state:

.. code:: python

    >>> target_file.write_text("Original content.\nSecond line.\n") 
    31

Execute the dry run:

.. code:: python

    >>> args_dry = parser.parse_args(["--dry-run", str(patch_file_path.resolve())])
    >>> ftw_app_dry = FtwPatch(args=args_dry)
    >>> ftw_app_dry.run() # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Applying patch from ...Path(...) in directory ...Path('.') 
    (strip=0, ws_norm=False, bl_ignore=False, all_ws_ignore=False).
    <BLANKLINE>
    --- Processing file: ...Path('target/file.txt') -> ...Path('target/file.txt') (1 hunks)
     - Applying Hunk 1/1 (@ Line 1: 2 -> 2)
     -> Patch successfully verified and stored in memory (2 lines).
    <BLANKLINE>
    Dry run completed. No files were modified.
    <BLANKLINE>
    Successfully processed 1 file changes.
    0
    
Verify the content remains unchanged:

.. code:: python

    >>> target_file.read_text()
    'Original content.\nSecond line.\n'

---

FtwPatch.run() Test Case 3: Strip Count (-p / --strip)
------------------------------------------------------

This test verifies the effect of `strip_count` on path resolution, simulating a patch created from a repository root.

.. dropdown:: Setup for strip count test ...
    :chevron: down-up
    :color: info

    .. code-block:: python
        
        >>> target_file_deep = Path("project/src/file_strip.py")
        >>> target_file_deep.parent.mkdir(parents=True, exist_ok=True)
        >>> target_file_deep.write_text("def old_function(): pass\n")
        25

        >>> strip_patch_content = """--- a/project/src/file_strip.py
        ... +++ b/project/src/file_strip.py
        ... @@ -1 +1 @@
        ... -def old_function(): pass
        ... +def new_function(): pass
        ... """
        >>> strip_patch_path = Path("../testinput/strip.diff")
        >>> strip_patch_path.write_text(strip_patch_content)
        128

        >>> print(target_file_deep.read_text())
        def old_function(): pass
        <BLANKLINE>

Target file content before stripping:

.. code:: python

    >>> target_file_deep.read_text()
    'def old_function(): pass\n'

Run Test Case: Strip Count `p=1`. This strips the leading path component ('a/') from the patch file:

.. code:: python

    >>> args_strip = parser.parse_args(["-p", "1", str(strip_patch_path.resolve())])
    >>> ftw_app_strip = FtwPatch(args=args_strip)
    >>> ftw_app_strip.run() # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Applying patch from ...Path(...) in directory ...Path('.') 
    (strip=1, ws_norm=False, bl_ignore=False, all_ws_ignore=False).
    <BLANKLINE>
    --- Processing file: ...Path('project/src/file_strip.py') -> ...Path('project/src/file_strip.py') (1 hunks)
     - Applying Hunk 1/1 (@ Line 1: 1 -> 1)
     -> Patch successfully verified and stored in memory (1 lines).
    <BLANKLINE>
    Starting write/delete phase: Applying changes to file system...
     -> Successfully wrote ...Path('project/src/file_strip.py').
    <BLANKLINE>
    Successfully processed 1 file changes.
    0
    
Verify the patch application:

.. code:: python

    >>> target_file_deep.read_text()
    'def new_function(): pass\n'

---

FtwPatch.run() Test Case 4: Whitespace Normalization
----------------------------------------------------

This section tests the FTW-specific normalization flags using a patch that intentionally contains differences in spacing and blank lines, causing a standard patch failure.

.. dropdown:: Setup for Whitespace Test ...
    :chevron: down-up
    :color: info

    .. code-block:: python
        
        >>> ws_target_file = Path("ws_target.py")
        >>> ws_target_file.write_text("def fn(): \n    pass  # End space\n\n    return\n\n\n")
        47

        >>> ws_patch_content = """--- ws_target.py
        ... +++ ws_target.py
        ... @@ -1,5 +1,4 @@
        ...  def fn():
        ... -    pass  # End space
        ... -
        ... -    return
        ... +    pass   # More space
        ... +    return
        ... """
        >>> ws_patch_path = Path("../testinput/ws_test.diff")
        >>> ws_patch_path.write_text(ws_patch_content)
        135

        >>> print(ws_target_file.read_text())
        def fn(): 
            pass  # End space
        <BLANKLINE>
            return
        <BLANKLINE>
        <BLANKLINE>
        <BLANKLINE>


Target file content before testing:

.. code:: python

    >>> ws_target_file.read_text()
    'def fn(): \n    pass  # End space\n\n    return\n\n\n'

Run Test Case 4a: Default Run. The patch should fail due to whitespace and blank line mismatches. We use `-v` to show the failure log:

.. code:: python

    >>> args_fail = parser.parse_args(["-v", str(ws_patch_path.resolve())])
    >>> ftw_app_fail = FtwPatch(args=args_fail)
    >>> ftw_app_fail.run() # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Applying patch...
    (strip=0, ws_norm=False, bl_ignore=False, all_ws_ignore=False).
    <BLANKLINE>
    --- Processing file: ...Path('ws_target.py') -> ...Path('ws_target.py') (1 hunks)
     - Applying Hunk 1/1 (@ Line 1: 5 -> 4)
    <BLANKLINE>
    Patch failed: Context mismatch in file 'ws_target.py' at expected line 1: Expected ''def fn():'', found ''def fn(): ''.
    1
    
    
Verify failure (Content must be unchanged):

.. code:: python

    >>> ws_target_file.read_text()
    'def fn(): \n    pass  # End space\n\n    return\n\n\n'

Run Test Case 4b: Normalize Non-Leading Whitespace. Revert the file and apply the patch using `--normalize-ws`. This ignores differences in spaces/tabs within lines:

.. code:: python

    >>> ws_target_file.write_text("def fn():\n    pass  # End space\n\n    return\n\n\n")
    46

.. code:: python

    >>> args_norm = parser.parse_args(["--normalize-ws", str(ws_patch_path.resolve())])
    >>> ftw_app_norm = FtwPatch(args=args_norm)
    >>> ftw_app_norm.run() # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Applying patch from ...Path('...') in directory ...Path('.') 
    (strip=0, ws_norm=True, bl_ignore=False, all_ws_ignore=False).
    <BLANKLINE>
    --- Processing file: ...Path('ws_target.py') -> ...Path('ws_target.py') (1 hunks)
     - Applying Hunk 1/1 (@ Line 1: 5 -> 4)
     -> Patch successfully verified and stored in memory (5 lines).
    <BLANKLINE>
    Starting write/delete phase: Applying changes to file system...
     -> Successfully wrote ...Path('ws_target.py').
    <BLANKLINE>
    Successfully processed 1 file changes.
    0
    
Verify success:

.. code:: python

    >>> ws_target_file.read_text()
    'def fn():\n    pass   # More space\n    return\n\n\n'

Run Test Case 4c: Ignore All Whitespace. Revert the file and apply the patch using `--ignore-all-ws`. This overrides other flags and handles all whitespace differences, including blank lines:

.. dropdown:: Setup testfile
    :chevron: down-up

    .. code:: python

        >>> ws_target_file.write_text("def fn():\n    pass  # End space\n\n    return\n\n\n")
        46

.. code:: python

    >>> args_all_ws = parser.parse_args(["--ignore-all-ws", str(ws_patch_path.resolve())])
    >>> ftw_app_all_ws = FtwPatch(args=args_all_ws)
    >>> ftw_app_all_ws.run() # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Applying patch from ...Path('...') in directory ...Path('.') 
    (strip=0, ws_norm=False, bl_ignore=False, all_ws_ignore=True).
    <BLANKLINE>
    --- Processing file: ...Path('ws_target.py') -> ...Path('ws_target.py') (1 hunks)
     - Applying Hunk 1/1 (@ Line 1: 5 -> 4)
     -> Patch successfully verified and stored in memory (5 lines).
    <BLANKLINE>
    Starting write/delete phase: Applying changes to file system...
     -> Successfully wrote ...Path('ws_target.py').
    <BLANKLINE>
    Successfully processed 1 file changes.
    0

Verify success:

.. code:: python

    >>> ws_target_file.read_text()
    'def fn():\n    pass   # More space\n    return\n\n\n'



FtwPatch.run() Test Case 5: Target File Missing
-----------------------------------------------

This test verifies the handling of a patch targeting a non-existent file when no creation flag is used.

.. dropdown:: Setup testfile
    :chevron: down-up
    :color: info

    .. code:: python

        >>> missing_target_patch_content = """--- missing_file.txt
        ... +++ missing_file.txt
        ... @@ -0,0 +1,1 @@
        ... +New content.
        ... """
        >>> missing_patch_path = Path("../testinput/missing.diff")
        >>> missing_patch_path.write_text(missing_target_patch_content)
        72

    >>> args_missing = parser.parse_args([str(missing_patch_path.resolve())])
    >>> ftw_app_missing = FtwPatch(args=args_missing)
    >>> ftw_app_missing.run() # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Applying patch...
    (strip=0, ws_norm=False, bl_ignore=False, all_ws_ignore=False).
    <BLANKLINE>
    --- Processing file: ...Path('missing_file.txt') -> ...Path('missing_file.txt') (1 hunks)
    <BLANKLINE>
    Patch failed: Original file not found for patching: ...Path('missing_file.txt')
    1

---

Tests for Pure Deletion Diff Patches
------------------------------------

Patches can also contain instructions that initiate the **deletion of a file**. This instruction is composed of two header lines in the unified diff format. Note that for **Windows operating systems**, `nul` should be used instead of `/dev/null`.

First, we set up the target directory where the file will be located.

.. dropdown:: Setup testfile
    :chevron: down-up
    :color: info

    .. code:: python
        

        >>> target_dir = Path("target")
        >>> target_dir.mkdir(exist_ok=True)

Next, we define the content of a **pure deletion patch**. The `+++ /dev/null` line signals that the new version of the file is empty, instructing the patching utility to delete the original file. We also define the target file's path.

.. code:: python

    >>> del_patch_content = """--- a/file_to_delete.txt
    ... +++ /dev/null
    ... """

    >>> target_file = target_dir / "file_to_delete.txt"

To make the patch applicable, we first create the target file temporarily and write the deletion patch content to a file.

.. dropdown:: Setup testfile
    :chevron: down-up
    :color: info

    .. code:: python

        >>> target_file.write_text("Diese Datei wird gelöscht.")
        26
        >>> del_patch_path = Path("../testinput/del_test.diff")
        >>> del_patch_path.write_text(del_patch_content)
        39

Now, we parse the command line arguments required to apply the patch. We specify the patch file path, the target directory, and set the strip count (`-p 1`).

.. code:: python

    >>> args = parser.parse_args([
    ...     str(del_patch_path), 
    ...     "-d", str(target_dir), 
    ...     "-p", "1"
    ... ])

We initialize the **`FtwPatch`** object with the parsed arguments.

.. code:: python

    >>> ftw_patcher = FtwPatch(args)

Before applying the patch, we verify that the file designated for deletion currently **exists** in the target directory.

>>> target_file.is_file()
True

Apply the patch. The output confirms that the file is marked for deletion and successfully removed during the write/delete phase.

.. code:: python

    >>> ftw_patcher.apply_patch() # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    Applying patch ...
    --- Processing file: ...Path('file_to_delete.txt') -> '/dev/null' ...
        -> Marked for deletion.
    Starting write/delete phase: Applying changes to file system...
        -> Successfully deleted ...Path('...file_to_delete.txt').
    Successfully processed 1 file changes.
    0

After successful patching, the target file **should no longer exist** on the file system.

.. code:: python

    >>> target_file.is_file()
    False


If the patch is accidentally used again, or if the file did not exist before the first application (as is the case now), the patching utility **will throw an error**. This tests the deletion error path (Lücken **1103–1106**) where the file to be deleted is not found.

.. code:: python


    >>> ftw_patcher.apply_patch() 
    Traceback (most recent call last):
            ...
    ftw.patch.ftw_patch.FtwPatchError: File to be deleted not found: PosixPath('target/file_to_delete.txt')








FtwPatch Cleanup
--------------------

.. dropdown:: Cleanup of all temporary files and directories created during testing.
    :chevron: down-up
    :color: info
    
    .. code:: python

        >>> for file_ in target_dir.iterdir():
        ...     file_.unlink()
        >>> target_dir.rmdir()
        >>> target_file_deep.unlink(missing_ok=True)
        >>> target_file_deep.parent.rmdir()
        >>> target_file_deep.parent.parent.rmdir()
        >>> ws_target_file.unlink(missing_ok=True)
        >>> patch_file_path.unlink(missing_ok=True)
        >>> strip_patch_path.unlink(missing_ok=True)
        >>> ws_patch_path.unlink(missing_ok=True)
        >>> missing_patch_path.unlink(missing_ok=True)



