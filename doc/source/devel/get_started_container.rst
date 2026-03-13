Get Started with Ftwpatch Container Classes
============================================

.. SECTION - SetUp

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

>>> from fitzzftw.patch.lines import HunkLine

>>> h_line1 = HunkLine("+  def test_fn(a:str, b:int): \n")

>>> hunk1.add_line(h_line1)

>>> len(hunk1)
1

>>> hunk1.lines
[HunkLine(Content: '  def test_fn(a:str, b:int): ', Prefix: '+')]

>>> h_line2 = HunkLine("+      ret = a + str(b)\n")
>>> h_line3 = HunkLine("+      return ret\n")

>>> hunk1.add_line(h_line2)
>>> hunk1.add_line(h_line3)

>>> len(hunk1)
3

>>> hunk1.lines # doctest: +NORMALIZE_WHITESPACE
[HunkLine(Content: '  def test_fn(a:str, b:int): ', Prefix: '+'),
 HunkLine(Content: '      ret = a + str(b)', Prefix: '+'), 
 HunkLine(Content: '      return ret', Prefix: '+')]

>>> hunk1[1]
HunkLine(Content: '      ret = a + str(b)', Prefix: '+')


>>> it_hunk1 = iter(hunk1)
>>> next(it_hunk1)
HunkLine(Content: '  def test_fn(a:str, b:int): ', Prefix: '+')

>>> for line in it_hunk1:
...     print(line)
HunkLine(Content: '      ret = a + str(b)', Prefix: '+')
HunkLine(Content: '      return ret', Prefix: '+')
