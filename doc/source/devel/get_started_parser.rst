Getting Started: Parser
=======================

The :mod:`.parser` module is the engine of the framework. It transforms raw 
patch data (strings) into a structured hierarchy of objects like 
:class:`~.container.DiffCodeFile` and :class:`~.container.Hunk`.

The Line Factory
----------------

The :class:`.parser.PatchParser` uses a central factory method to categorize 
every line of a patch. This ensures that the correct specialized class is 
instantiated based on the line's prefix.

    >>> from fitzzftw.patch.parser import PatchParser
    >>> from fitzzftw.patch.lines import HeadLine, HunkHeadLine, HunkLine

    >>> parser = PatchParser()
    
Testing the factory with different line types

    >>> type(parser.create_line("--- old_file.py")) == HeadLine
    True
    >>> type(parser.create_line("@@ -1,1 +1,1 @@")) == HunkHeadLine
    True
    >>> type(parser.create_line("+ added line")) == HunkLine
    True

The Line Stream
---------------

The method :meth:`~.PatchParser.get_lines` is a generator that converts 
strings into specialized line objects.

    >>> from fitzzftw.patch.parser import PatchParser
    >>> parser = PatchParser()
    >>> stream = ["--- a/file.txt", "+++ b/file.txt", "+new content"]
    >>> lines = list(parser.get_lines(stream))
    >>> lines[0]
    HeadLine(Content: 'a/file.txt', Prefix: '--- ')
    >>> lines[2]
    HunkLine(Content: 'new content', Prefix: '+')


Parsing a Patch Stream
----------------------

The parser works as a generator. It processes an iterable of strings (like a 
file object or a list of lines) and yields :class:`~.container.DiffCodeFile` 
objects. This "streaming" approach is memory efficient for large patches.

Here is a minimal example of parsing a raw diff string:

    >>> diff_data = [
    ...     "--- a/test.txt",
    ...     "+++ b/test.txt",
    ...     "@@ -1,1 +1,1 @@",
    ...     "-old content",
    ...     "+new content"
    ... ]
    
    >>> files = list(parser.iter_files(diff_data))
    >>> len(files)
    1

    >>> patch_file = files[0]
    >>> patch_file.orig_header
    HeadLine(Content: 'a/test.txt', Prefix: '--- ')

    >>> len(patch_file.hunks)
    1


Handling Git Diff Noise
-----------------------

Real-world diffs (like those from ``git diff``) often contain irrelevant 
metadata (e.g., index, mode, or extended headers). The parser is designed 
to be **tolerant**: it safely ignores unknown lines and only processes 
structurally relevant data.

Git metadata or random text is ignored

    >>> noise = [
    ...     "diff --git a/test.txt b/test.txt",
    ...     "index 0000000..1234567",
    ...     "--- a/test.txt",
    ...     "+++ b/test.txt",
    ...     "@@ -1,1 +1,1 @@",
    ...     "-old content",
    ...     "+new content"
    ... ]
    
    >>> files = list(parser.iter_files(noise))
    >>> len(files)
    1
    >>> files[0].orig_header
    HeadLine(Content: 'a/test.txt', Prefix: '--- ')



Error Handling
--------------

While the parser ignores noise, it still validates the **sequence** of the 
patch. If data appears in an impossible order (e.g., a hunk starts without 
a preceding file header), it raises a :class:`~.exceptions.PatchParseError`.

A hunk header without leading '---' / '+++' headers is invalid

    >>> invalid_structure = ["@@ -1,1 +1,1 @@", "+added"]
    >>> list(parser.iter_files(invalid_structure))
    Traceback (most recent call last):
        ...
    fitzzftw.patch.exceptions.PatchParseError: Line 1: Found '@@ ' before file headers
