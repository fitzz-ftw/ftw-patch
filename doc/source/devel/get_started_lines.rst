
Getting Started with Line Classes from Patch Module 
===================================================

:Author: Fitzz TeΧnik Welt
:Email: FitzzTeXnikWelt@t-online.de

This document provides a step-by-step introduction and executable documentation 
for the core line logic in the :mod:`fitzzftw.patch` module.



.. SECTION - PatchLine

Class PatchLine 
----------------

.. code:: python 

    >>> from pathlib import Path
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

.. !SECTION

.. SECTION - FileLine

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

.. !SECTION

.. SECTION - HunkLinie

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
   fitzzftw.patch.exceptions.PatchParseError: Hunk content line missing valid prefix 
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

   >>> from fitzzftw.patch.static import colors
   >>> colors.switch_to_testmode()

   >>> hl_ws.print() # doctest: +NORMALIZE_WHITESPACE
   grn>+  def test_fn(  a, b ):         <reset


.. !SECTION

.. SECTION - HunkHeadLine

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

    >>> hhline2.print()
    cyn>@@ -10,4 +10,6 @@ class DatabaseConnector:<reset


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

.. !SECTION

.. SECTION - HeadLine

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


    >>> hline1.print()
    red>--- target/file.txt<reset


    >>> hline2.print() # doctest: +NORMALIZE_WHITESPACE
    grn>+++ b/src/new_module.py (metadata: created on 2025-12-21)<reset

.. !SECTION
