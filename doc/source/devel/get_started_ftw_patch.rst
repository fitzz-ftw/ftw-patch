.. role:: py:mod(strong)
.. role:: py:func(strong)
.. role:: py:meth(strong)
.. role:: py:class(strong)

.. _ftw-patch-intro:

ftw_patch: Getting Started with Patch Application
=================================================

:Author: Fitzz TeXnik Welt
:Email: FitzzTeXnikWelt@t-online.de

This document provides a step-by-step introduction and executable documentation for the core logic in the ``ftw_patch`` module.

.. seealso:: The full API documentation for the module is available here: :py:mod:`ftw_patch.ftw_patch`

---

.. _ftw-patch-setup-env:

..
    Environment Setup and Path Initialization
    -----------------------------------------

    **Important Note for Users:** The following code blocks (Sections 1 through 3) are **only used to set up an isolated test environment** for the DocTests. These steps are required for the tests to run correctly and ensure test coverage. As an end-user or reader of the documentation, you **do not need to understand or run** this code; it is solely for information about the test conditions.

    The setup is divided into three separate DocTest blocks. Since these commands produce no output, they appear as compact executable lines in the rendered document.

    1. Module Imports
    ~~~~~~~~~~~~~~~~~
.. code:: python
    :hidden:

    >>> import os
    >>> import sys
    >>> from pathlib import Path

..
    1. Global Variable Definitions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python
    :hidden:

    >>> TEST_BASEDIR = Path("doc/source/devel/testhome")
    >>> TEST_INPUT = TEST_BASEDIR / "testinput"
    >>> TEST_CWD = TEST_BASEDIR / "testoutput"

..
    1. File System and Environment Setup
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python
    :hidden:

    >>> TEST_BASEDIR.mkdir(parents=True, exist_ok=True)
    >>> os.environ['HOME'] = str(TEST_BASEDIR.resolve())
    >>> TEST_INPUT.mkdir(parents=True, exist_ok=True)
    >>> TEST_CWD.mkdir(parents=True, exist_ok=True)
    >>> CONFIG_DIR = TEST_BASEDIR / ".config/ftw"
    >>> CONFIG_DIR.mkdir(parents=True, exist_ok=True)

..
    Verification using path abstraction to ensure environment is set:

.. code:: python
    :hidden:

    >>> expected_suffix = 'doc/source/devel/testhome'
    >>> resolved_home = os.environ['HOME']
    >>> start_index = resolved_home.rfind(expected_suffix)
    >>> print(f"HOME set to: .../{resolved_home[start_index:]}") # doctest: +ELLIPSIS
    HOME set to: .../doc/source/devel/testhome
    >>> print(f"TEST_CWD (Write): {TEST_CWD.name}")
    TEST_CWD (Write): testoutput
    >>> os.chdir(TEST_CWD)

..
    ---
..
    Temporary Patch File Setup
    --------------------------

    We create a dummy patch file in the CWD (`TEST_CWD`) to allow the **FtwPatch class initialization** to succeed the file existence check.

    .. code:: python

        >>> dummy_patch_file = Path("patch.diff")
        >>> dummy_patch_file.touch()


..
    Understanding the Current Working Directory (CWD)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The variable **`TEST_CWD`** (`testoutput`) defines the isolated 
    location where files are created and patched. In the subsequent 
    tests, we intentionally switch the **Current Working Directory 
    (CWD)** to this path using `with Path(TEST_CWD).cwd():`. This 
    means all **relative paths** used within those test blocks 
    (like calling the patch on `./target/file.txt`) are relative 
    to `TEST_CWD`.

    ---

.. _ftw-patch-get-argparser-func:

_get_argparser() Function (Utility)
-----------------------------------

This utility function parses the command-line arguments. We verify the defaults and argument parsing here.

First, import the necessary component:

.. code:: python

    >>> from ftw_patch.ftw_patch import _get_argparser 

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
--------------------------------------

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

---

.. _ftw-patch-dry-run:

Test Case 3: Handling Dry Run (--dry-run)
----------------------------------

This test confirms that the boolean flag `dry_run` is correctly set.

Test with the `--dry-run` flag present:

.. code:: python

    >>> args_dry = parser.parse_args(["--dry-run", "patch.diff"])
    >>> args_dry.dry_run
    True

---

.. _ftw-patch-verbose:

Test Case 4: Controlling Verbosity (-v)
---------------------------------------

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

.. _ftw-patch-class-init:

FtwPatch Class Initialization
-----------------------------

The :py:class:`ftw_patch.ftw_patch.FtwPatch` class encapsulates the patching logic.

First, import the class and its custom exception:

.. code:: python

    >>> from ftw_patch.ftw_patch import FtwPatch, FtwPatchError

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

..
    Setup for patching (Hidden):

    .. code-block:: python
        :hidden:

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

..
    Setup for strip count test (Hidden):

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

..
    Setup for Whitespace Test (Hidden):

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
    :hidden:

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

.. code:: python
    :hidden:

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



HunkLine
========

The HunkLine class is implemented in the Patch Parser to encapsulate hunk line content and manage whitespace normalization.

.. code:: python

   >>> from ftw_patch.ftw_patch import HunkLine, PatchParseError

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
   ftw_patch.ftw_patch.PatchParseError: Hunk content line missing valid prefix (' ', '+', '-') or is empty: 'Missing prefix'

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




..
    ---

    .. _ftw-patch-cleanup:

    Environment Cleanup
    -------------------

    Final cleanup to ensure the environment is left in a clean state (Hidden):

    .. code-block:: python
        # doctest: +SKIP
        # Clean up all files created during testing
        
        ws_target_file.unlink()
        ws_patch_path.unlink()
        
        target_file_deep.unlink()
        target_file_deep.parent.rmdir()
        target_file_deep.parent.parent.rmdir()
        
        target_file.unlink() 
        target_dir.rmdir()
        patch_file_path.unlink()
        strip_patch_path.unlink()
        
        # Final verification: All test files should be gone
        ws_target_file.exists()
        False