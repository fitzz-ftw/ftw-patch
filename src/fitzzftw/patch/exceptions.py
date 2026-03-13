"""
exceptions
===============================

| File: src/fitzzftw/patch/exceptions.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de
| License: LGPLv2 or above

Modul exceptions documentation
"""

from collections.abc import Callable
from inspect import Signature, isfunction, ismethod, signature
from pathlib import Path
from typing import Any, get_type_hints

#SECTION - Helperfunctions and -classes

def get_string_of_type(protocol_type) -> str:
    if hasattr(protocol_type, "__name__"):
        ret = protocol_type.__name__
    else:
        ret = protocol_type
    return ret

def protocol_error_message(obj: Callable | None, argument: str, *protocols) -> str:
    ret = []
    mfw = FtwMethFuncWrap(obj)
    if mfw:
        ret.append(f"Error: {mfw.name} for {argument}")
    protokoll: list = [prot for prot in protocols if prot._is_runtime_protocol]
    if len(protokoll) > 1:
        ret.append("Please implement one of:")
    else:
        ret.append("Please implement:")
    protocol = FtwProtocolWrap()
    for prot in protokoll:
        protocol.set_new_protocol(prot)
        ret.append(f"  {protocol.name}:")
        if protocol.non_callable:
            ret.append("    Args:")
            for item in sorted(protocol.non_callable):
                ret.append(f"      {item}: {protocol.annontations[item]}")
        if protocol.callable:
            ret.append("    Meth:")
            for item in sorted(protocol.callable):
                ret.append(f"      {item}{protocol.signatures[item]}")
    if mfw:
        ret.append(f"or\n  overwrite {mfw}.")
    return "\n".join(ret)

class FtwProtocolWrap:
    def __init__(self, protocol=None) -> None:
        if protocol:
            self.set_new_protocol(protocol)

    def set_new_protocol(self, protocol) -> None:
        self._name: str = protocol.__name__
        self._annontations: dict[str, Any] = {
            k: get_string_of_type(v) for (k, v) in get_type_hints(protocol).items()
        }
        self._attributes: set[str] = protocol.__dict__["__protocol_attrs__"]
        self._non_callable: set[str] = protocol.__non_callable_proto_members__
        self._callable: set[str] = self._attributes - self._non_callable
        self._signatures: dict[str, str] = {}
        for call in sorted(self._callable):
            self._signatures[call] = str(signature(protocol.__dict__[call]))

    @property
    def name(self) -> str:
        return self._name or ""

    @property
    def non_callable(self) -> set[str]:
        return self._non_callable or set()

    @property
    def callable(self) -> set[str]:
        return self._callable or set()

    @property
    def annontations(self) -> dict[str, Any]:
        return self._annontations or {}

    @property
    def attributes(self) -> set[str]:
        return self._attributes or set()

    @property
    def signatures(self) -> dict[str, str]:
        return self._signatures or {}

class FtwMethFuncWrap:
    def __init__(self, meth_func: Callable | None = None):
        if meth_func is None:
            self._len: int = 0
            self._name: str =""
            self._is_methode: bool = False
            self._is_function: bool = False
            return
        self._len: int = 1
        self._signature: Signature = signature(meth_func)
        self._name: str = meth_func.__qualname__
        self._is_methode: bool = ismethod(meth_func)
        self._is_function: bool = isfunction(meth_func)
        if self._is_function and "." in self._name:
            self._is_methode = True
            self._is_function = False

    @property
    def is_methode(self) -> bool:
        return self._is_methode

    @property
    def is_function(self) -> bool:
        return self._is_function

    @property
    def is_empty(self) -> bool:
        return self._len <= 0

    @property
    def name(self) -> str:
        return self._name

    def __len__(self) -> int:
        return self._len

    def __str__(self):
        if self.is_empty:
            return str(None)
        sig: str = str(self._signature)
        if self._is_methode:
            if not sig.startswith("(self"):
                # if not len(self._signature.parameters):
                #     print("treffer")
                #     sig = "".join(["(self", sig.lstrip("(")])
                # else:
                    sig = ", ".join(["(self", sig.lstrip("(")])
        return f"{self._name}{sig}"

#!SECTION - Helperfunctions and -classes

#SECTION --- Exceptions ---

class FtwException(Exception):
    """
    Base exception for all exceptions raised by the ``ftw``
    module.

    **Inheritance Hierarchy**
        * :py:class:`FtwException`
        * :py:class:`Exception`
    """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)!r})"

#SECTION ----Errors-----

class FtwError(FtwException):
    """
    Base exception for all errors raised by the :py:mod:`fitzzftw`
    namespace.

    **Inheritance Hierarchy**
        * :py:class:`FtwError`
        * :py:class:`FtwException`
        * :py:class:`Exception`
    """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)!r})"

class FtwProtcolError(FtwError):
    """
    Raised when an operation or function is applied to an object of inappropriate
    protocol type.

**Inheritance Hierarchy**
    * :py:class:`FtwProtocolError`
    * :py:class:`FtwError`
    * :py:class:`FtwException`
    * :py:class:`Exception`

    """

    def __init__(self, meth_func: Callable, arg_name: str, protocols: tuple) -> None:
        super().__init__()
        self._meth_func: Callable = meth_func
        self._arg_name: str = arg_name
        self._protocols: tuple = protocols

    def __str__(self) -> str:
        return f"\n{protocol_error_message(self._meth_func, self._arg_name, *self._protocols)}"

class FtwPatchError(FtwError):  
    """
    Base exception for all errors raised by the :py:mod:`ftw_patch`
    module.

    **Inheritance Hierarchy**
        * :py:class:`FtwPatchError`
        * :py:class:`FtwError`
        * :py:class:`FtwException`
        * :py:class:`Exception`
    """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)!r})"

class PatchParseError(FtwPatchError):  
    """
    Exception raised when an error occurs during the parsing of the
    patch file content.

    **Inheritance Hierarchy**
        * :py:class:`PatchParseError`
        * :py:class:`FtwPatchError`
        * :py:class:`FtwException`
        * :py:class:`Exception`
    """

    def __init__(self, message: str) -> None:
        """
        Initializes the PatchParseError.

        :param message: The error message.
        """
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)!r})"
        # return f"{self.__class__.__name__}(message={self.args[0]!r})"



#!SECTION ----Errors-----
#!SECTION --- Exceptions ---

if __name__ == "__main__":  # pragma: no cover
    from doctest import FAIL_FAST, testfile
    
    be_verbose = False
    be_verbose = True
    option_flags = 0
    option_flags = FAIL_FAST
    test_sum = 0
    test_failed = 0
    
    # Pfad zu den dokumentierenden Tests
    testfiles_dir = Path(__file__).parents[3] / "doc/source/devel"
    test_file = testfiles_dir / "get_started_exceptions.rst"
    # test_file = testfiles_dir / "get_started_ftw_patch.rst"

    if test_file.exists():
        print(f"--- Running Doctest for {test_file.name} ---")
        doctestresult = testfile(
            str(test_file),
            module_relative=False,
            verbose=be_verbose,
            optionflags=option_flags,
        )
        test_failed += doctestresult.failed
        test_sum += doctestresult.attempted
        if test_failed == 0:
            print(f"\nDocTests passed without errors, {test_sum} tests.")
        else:
            print(f"\nDocTests failed: {test_failed} tests.")
    else:
        print(f"⚠️ Warning: Test file {test_file.name} not found.")
