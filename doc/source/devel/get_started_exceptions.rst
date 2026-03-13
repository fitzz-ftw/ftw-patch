Get Started with Ftwpatch Exception Classes
============================================

>>> str
<class 'str'>

>>> from fitzzftw.patch.exceptions import get_string_of_type
>>> get_string_of_type(str)
'str'

.. CLASS - FtwProtocolWrap 

>>> from fitzzftw.patch.exceptions import FtwProtocolWrap

>>> from fitzzftw.patch.protocols import LineLike

.. SECTION - Without methods

>>> protocol1 = FtwProtocolWrap(LineLike)

>>> protocol1.name
'LineLike'

>>> type(protocol1.non_callable) == set
True

>>> sorted(protocol1.non_callable)
['_color_map', 'orig_line', 'prefix']


>>> type(protocol1.callable) == set
True

>>> sorted(protocol1.callable)
[]


>>> protocol1.annontations
{'_color_map': 'dict', 'prefix': str | None, 'orig_line': 'str'}

>>> type(protocol1.attributes) == set
True

>>> sorted(protocol1.attributes)
['_color_map', 'orig_line', 'prefix']

>>> protocol1.signatures
{}

.. !SECTION

.. SECTION - With methodes in protocol

>>> from typing import Protocol

>>> class LineLike2(LineLike,Protocol):
...     def test(self) -> str: ...
...     def test2(self, a: int) -> None: ...

>>> dir(LineLike2)
['__abstractmethods__', '__annotations__', '__class__', '__class_getitem__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__firstlineno__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__non_callable_proto_members__', '__parameters__', '__protocol_attrs__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__static_attributes__', '__str__', '__subclasshook__', '__weakref__', '_abc_impl', '_is_protocol', '_is_runtime_protocol', 'test', 'test2']

>>> dir(LineLike)
['__abstractmethods__', '__annotations__', '__class__', '__class_getitem__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__firstlineno__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__non_callable_proto_members__', '__parameters__', '__protocol_attrs__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__static_attributes__', '__str__', '__subclasshook__', '__weakref__', '_abc_impl', '_is_protocol', '_is_runtime_protocol']

>>> dir(LineLike2.__dict__)
['__class__', '__class_getitem__', '__contains__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__ior__', '__iter__', '__le__', '__len__', '__lt__', '__ne__', '__new__', '__or__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__ror__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 'copy', 'get', 'items', 'keys', 'values']

>>> dir(LineLike.__dict__)
['__class__', '__class_getitem__', '__contains__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__ior__', '__iter__', '__le__', '__len__', '__lt__', '__ne__', '__new__', '__or__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__ror__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 'copy', 'get', 'items', 'keys', 'values']

>>> LineLike2.__dict__.keys() # doctest: +ELLIPSIS
dict_keys(['__module__', '__firstlineno__', 'test', 'test2', '__static_attributes__', '__doc__', '__parameters__', '_is_protocol', '__subclasshook__', '__abstractmethods__', '_abc_impl', '__annotations__', '__protocol_attrs__'])

>>> LineLike.__dict__.keys()
dict_keys(['__module__', '__firstlineno__', '__annotations__', '__doc__', '__static_attributes__', '__dict__', '__weakref__', '__parameters__', '_is_protocol', '__subclasshook__', '__init__', '__abstractmethods__', '_abc_impl', '__protocol_attrs__', '_is_runtime_protocol', '__non_callable_proto_members__'])

>>> li_2 = list(LineLike2.__non_callable_proto_members__)
>>> li_2.sort()

>>> li_1 = list(LineLike.__non_callable_proto_members__)
>>> li_1.sort()

>>> li_2
['_color_map', 'orig_line', 'prefix']

>>> li_1
['_color_map', 'orig_line', 'prefix']

>>> protocol1.set_new_protocol(LineLike2)

>>> protocol1.name
'LineLike2'

>>> type(protocol1.non_callable) == set
True

>>> sorted(protocol1.non_callable)
['_color_map', 'orig_line', 'prefix']

>>> type(protocol1.callable) == set
True

>>> sorted(protocol1.callable)
['test', 'test2']


>>> protocol1.annontations
{'_color_map': 'dict', 'prefix': str | None, 'orig_line': 'str'}

>>> type(protocol1.attributes) == set
True

>>> sorted(protocol1.attributes)
['_color_map', 'orig_line', 'prefix', 'test', 'test2']

>>> protocol1.signatures
{'test': '(self) -> str', 'test2': '(self, a: int) -> None'}

.. !SECTION 

.. !CLASS

.. CLASS - FtwMethFuncWrap

.. SECTION - With Function 

>>> from fitzzftw.patch.exceptions import FtwMethFuncWrap

>>> function1 = FtwMethFuncWrap(get_string_of_type)
>>> function1.name
'get_string_of_type'

>>> function1.is_methode
False

>>> function1.is_function
True

>>> function1.is_empty
False

>>> len(function1)
1

>>> print(function1)
get_string_of_type(protocol_type) -> str

.. !SECTION

.. SECTION - Without Function

>>> function2 = FtwMethFuncWrap()
>>> function2.name
''

>>> function2.is_methode
False

>>> function2.is_function
False

>>> function2.is_empty
True

>>> len(function2)
0

>>> print(function2)
None

.. !SECTION

>>> from fitzzftw.patch.container import Hunk

>>> hunk_apply = FtwMethFuncWrap(Hunk.apply)

>>> hunk_apply.name
'Hunk.apply'

>>> hunk_apply.is_methode
True

>>> hunk_apply.is_function
False

>>> hunk_apply.is_empty
False

>>> len(hunk_apply)
1

>>> print(hunk_apply) #doctest: +NORMALIZE_WHITESPACE
Hunk.apply(self, 
    lines: list[fitzzftw.patch.lines.FileLine], 
    options: fitzzftw.patch.protocols.HunkCompareOptions) 
    -> list[fitzzftw.patch.lines.FileLine]

>>> hunk_lines = FtwMethFuncWrap(Hunk.lines) #doctest: +ELLIPSIS
Traceback (most recent call last):
    ...
TypeError: <property object at 0x7...> is not a callable object

>>> hunk_repr = FtwMethFuncWrap(Hunk.__repr__)

>>> print(hunk_repr)
Hunk.__repr__(self) -> str

.. !CLASS

.. FUNCTION - protocol_error_message

>>> from fitzzftw.patch.exceptions import protocol_error_message

>>> protocol_error_message(None, "test", LineLike) # doctest: +NORMALIZE_WHITESPACE
'Please implement:\n  LineLike:\n    Args:\n      _color_map: dict\n      
    orig_line: str\n      prefix: str | None'

>>> protocol_error_message(None, "test", LineLike, LineLike2) # doctest: +NORMALIZE_WHITESPACE
'Please implement one of:\n  
  LineLike:\n    
    Args:\n      
      _color_map: dict\n      
      orig_line: str\n      
      prefix: str | None\n  
  LineLike2:\n    
    Args:\n      
      _color_map: dict\n      
      orig_line: str\n      
      prefix: str | None\n    
    Meth:\n      
      test(self) -> str\n      
      test2(self, a: int) -> None'

>>> from typing import runtime_checkable

>>> @runtime_checkable
... class PrinterLike(Protocol):
...     def bwprint(self, text:str, invers:bool)-> bool:... 
...     def colorprint(self, text:str, invers:bool, fcolor:str, bcolor:str)-> bool:... 
...     def empty_page(self)->bool:...

>>> protocol_error_message(None, "test", LineLike, LineLike2, PrinterLike) # doctest: +NORMALIZE_WHITESPACE
'Please implement one of:\n  
  LineLike:\n    
    Args:\n      
      _color_map: dict\n      
      orig_line: str\n      
      prefix: str | None\n  
  LineLike2:\n    
    Args:\n      
      _color_map: dict\n      
      orig_line: str\n      
      prefix: str | None\n    
    Meth:\n      
      test(self) -> str\n      
      test2(self, a: int) -> None\n  
  PrinterLike:\n    
    Meth:\n      
      bwprint(self, text: str, invers: bool) -> bool\n      
      colorprint(self, text: str, invers: bool, fcolor: str, bcolor: str) -> bool\n      
      empty_page(self) -> bool'


>>> from fitzzftw.patch.exceptions import FtwException

>>> exception = FtwException("Only an Exception")
>>> exception
FtwException('Only an Exception')

>>> from fitzzftw.patch.exceptions import FtwError
>>> error = FtwError("Attention an Error")
>>> error 
FtwError('Attention an Error')


.. !FUNCTION
