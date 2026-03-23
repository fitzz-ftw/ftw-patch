Get Started with Ftwpatch Container Classes
============================================

The :class:`.container.Hunk` class is the primary container for diff data. It manages a group of 
lines belonging to a specific change block within a patch.

To begin, you need a header line (the ``@@`` line) to define the context for the hunk:

.. SECTION - SetUp

Once the header is defined, you can initialize the :class:`~fitzzftw.patch.container.Hunk` object. At this stage, the 
container is empty but already knows its starting positions in the old and new files:

>>> from fitzzftw.patch.lines import HunkHeadLine
>>> hh_line = HunkHeadLine("@@ -1,2 +1,3 @@")

.. !SECTION

>>> from fitzzftw.patch.container import Hunk
>>> hunk1 = Hunk(hh_line)
>>> hunk1
Hunk(header=(1, 2, 1, 3), lines=0)

>>> hunk1.old_start
1

>>> hunk1.new_start
1

>>> hunk1.lines
[]

>>> len(hunk1)
0

To populate the hunk, you add :class:`.lines.HunkLine` objects. 
Each line represents a single change (addition, deletion, or context). 
Adding a line increases the length of the hunk:

>>> from fitzzftw.patch.lines import HunkLine

>>> h_line1 = HunkLine("+  def test_fn(a:str, b:int): \n")

>>> hunk1.add_line(h_line1)

>>> len(hunk1)
1

The :class:`~fitzzftw.patch.container.Hunk` container preserves the prefix (like ``+``) and the content separately 
for each line. You can continue adding lines to build the full code block:

>>> hunk1.lines
[HunkLine(Content: '  def test_fn(a:str, b:int): ', Prefix: '+')]

>>> h_line2 = HunkLine("+      ret = a + str(b)\n")
>>> h_line3 = HunkLine("+      return ret\n")

>>> hunk1.add_line(h_line2)
>>> hunk1.add_line(h_line3)

>>> len(hunk1)
3

The :class:`.container.Hunk` tracks line changes automatically as you add them:

>>> hunk1.addedlines
3
>>> hunk1.deletedlines
0

Adding a deletion line

>>> h_del = HunkLine("-      old_code()\n")
>>> hunk1.add_line(h_del)
>>> hunk1.deletedlines
1

This :class:`Hunk` is unbound.

>>> hunk1.parent is None 
True

The container acts like a standard Python :class:`~python.list`, allowing you to inspect all lines 
at once, access specific lines by their index, or iterate through them:

>>> hunk1.lines # doctest: +NORMALIZE_WHITESPACE
[HunkLine(Content: '  def test_fn(a:str, b:int): ', Prefix: '+'),
 HunkLine(Content: '      ret = a + str(b)', Prefix: '+'), 
 HunkLine(Content: '      return ret', Prefix: '+'),
 HunkLine(Content: '      old_code()', Prefix: '-')]

>>> hunk1[1]
HunkLine(Content: '      ret = a + str(b)', Prefix: '+')


>>> it_hunk1 = iter(hunk1)
>>> next(it_hunk1)
HunkLine(Content: '  def test_fn(a:str, b:int): ', Prefix: '+')

>>> for line in it_hunk1:
...     print(line)
HunkLine(Content: '      ret = a + str(b)', Prefix: '+')
HunkLine(Content: '      return ret', Prefix: '+')
HunkLine(Content: '      old_code()', Prefix: '-')

Working with DiffCodeFile Containers
--------------------------------------

The :class:`.container.DiffCodeFile` class acts as the central assembly point for a 
single file's modifications within a patch. It manages the file headers 
(--- and +++) and coordinates the collection of hunks.

To initialize a file container, you must provide a valid original header (the ``---`` line):

.. SECTION - SetUp

>>> from fitzzftw.patch.lines import HeadLine
>>> from fitzzftw.patch.container import DiffCodeFile

Setup for internal logic

>>> h1 = HeadLine("--- a/test.py")
>>> h2 = HeadLine("+++ b/test.py")

.. !SECTION

>>> diff_file = DiffCodeFile(h1)
>>> diff_file
DiffCodeFile(orig=a/test.py, hunks=0)

The class ensures that the file starts with a proper original header. Once 
initialized, you can set the target header (the ``+++`` line) via the ``new_header`` property:

>>> diff_file.new_header = h2
>>> diff_file.new_header.content
'b/test.py'

A :class:`~fitzzftw.patch.container.DiffCodeFile` serves as a list-like container 
for :class:`~fitzzftw.patch.container.Hunk` objects. 
You can add hunks as they are parsed from the patch file:

>>> hh = HunkHeadLine("@@ -1,1 +1,1 @@")
>>> hunk = Hunk(hh)
>>> diff_file.add_hunk(hunk)
>>> len(diff_file)
1

Just like the :class:`~fitzzftw.patch.container.Hunk` container, 
:class:`~fitzzftw.patch.container.DiffCodeFile` supports indexed access and 
iteration, making it easy to inspect all changes planned for this specific file:

>>> first_hunk = diff_file[0]
>>> first_hunk
Hunk(header=(1, 1, 1, 1), lines=0)

>>> for hunk in diff_file:
...     print(f"Processing hunk starting at line {hunk.old_start}")
Processing hunk starting at line 1

The container also provides helper methods to resolve file paths based 
on the header information, which is essential for applying the patch later:

>>> diff_file.get_source_path().as_posix()
'a/test.py'

>>> diff_file.get_source_path(strip=1).as_posix()
'test.py'

>>> diff_file.addedlines
0

>>> diff_file.deletedlines
0

>>> diff_file.add_hunk(hunk1)
>>> diff_file.addedlines
3

>>> diff_file.deletedlines
1

>>> hunk1.parent=None
Traceback (most recent call last):
    ...
fitzzftw.patch.exceptions.FtwPatchError: Hunk parent cannot be set to None!

>>> hunk1.parent= diff_file
Traceback (most recent call last):
    ...
fitzzftw.patch.exceptions.FtwPatchError: Hunk parent is already set and cannot be changed!

>>> hunk1.parent == diff_file
True

>>> diff_file_hunk1 = hunk1.parent
>>> diff_file_hunk1.hunks # doctest: +NORMALIZE_WHITESPACE
[Hunk(header=(1, 1, 1, 1), lines=0), 
 Hunk(header=(1, 2, 1, 3), lines=4)]


>>> diff_error = DiffCodeFile(h1)
>>> diff_error.get_target_path()
Traceback (most recent call last):
    ...
ValueError: New Header is None
