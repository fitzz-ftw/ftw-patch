# File: src/fitzzftw/patch/exceptions.py
# Author: Fitzz TeXnik Welt
# Email: FitzzTeXnikWelt@t-online.de
# License: LGPLv2 or above

"""
:mod:`.exceptions`
===============================

This module provides a specialized hierarchy of exceptions for the fitzzftw framework.
Beyond standard error handling, it includes advanced introspection tools for
Python Protocols and callables.

Core Features:
--------------
* **Protocol Validation**: 
  Uses :class:`.FtwProtocolWrap` and :class:`.FtwProtocolError` to generate
  highly detailed error messages when objects do not match required interfaces.
* **Signature Inspection**: 
  Employs :class:`.FtwMethFuncWrap` to accurately represent
  methods and functions (including 'self' injection) in diagnostic outputs.
* **Type Awareness**: 
  Automatically resolves type names and hints into human-readable
  strings for clearer debugging.g

The primary goal of this module is to turn cryptic "TypeError" or "AttributeError"
messages into actionable implementation guides for the developer.
"""
from collections.abc import Callable
from inspect import Signature, isfunction, ismethod, signature
from pathlib import Path
from typing import Any, get_type_hints

#SECTION - Helperfunctions and -classes

def get_string_of_type(protocol_type) -> str:
    """
    Extracts a human-readable string representation of a type.

    This helper is used during protocol introspection to handle both actual
    class objects and pre-defined type strings. If the input has a '__name__'
    attribute (e.g., a class), it returns that name; otherwise, it returns
    the input as is.

    :param protocol_type: The type object or string to convert.
    :returns: A string representation of the type.
    """
    if hasattr(protocol_type, "__name__"):
        ret = protocol_type.__name__
    else:
        ret = protocol_type
    return ret

def protocol_error_message(obj: Callable | None, argument: str, *protocols) -> str:
    """
    Constructs a detailed, human-readable error message for protocol violations.

    The message identifies the failing function and argument, then lists the
    requirements of the expected protocols (both data attributes and methods).
    It provides a clear blueprint of what needs to be implemented or overridden.

    :param obj: The callable (function or method) where the error occurred.
    :param argument: The name of the argument that failed the protocol check.
    :param protocols: A variable number of protocol classes to check against.
    :returns: A formatted string containing the error details and requirements.
    """
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
                ret.append(f"      {item}: {protocol.annotations[item]}")
        if protocol.callable:
            ret.append("    Meth:")
            for item in sorted(protocol.callable):
                ret.append(f"      {item}{protocol.signatures[item]}")
    if mfw:
        ret.append(f"or\n  overwrite {mfw}.")
    return "\n".join(ret)

class FtwProtocolWrap:
    """
    A metadata wrapper for Python Protocol classes.

    This class introspects a given Protocol to extract its structural definition,
    including type hints, mandatory attributes, and method signatures. It serves
    as a bridge for documentation or validation tools that need to inspect
    protocol requirements without interacting with the original class directly.

    Attributes:
        _name (str): The name of the wrapped protocol.
        _annotations (dict): Mapping of attribute/method names to their type hint strings.
        _attributes (set): All members defined as part of the protocol.
        _non_callable (set): Protocol members that are data attributes.
        _callable (set): Protocol members that are methods.
        _signatures (dict): Mapping of method names to their stringified inspect.Signature.
    """
    def __init__(self, protocol=None) -> None:
        """
        Initializes the wrapper. If a protocol is provided, it is processed immediately.

        :param protocol: The Protocol class to inspect.
        """
        if protocol:
            self.set_new_protocol(protocol)

    def set_new_protocol(self, protocol) -> None:
        """
        Introspects the given protocol and populates all metadata fields.

        This method extracts:
        1. Type hints for all members.
        2. Required protocol attributes via '__protocol_attrs__'.
        3. Separation of callable (methods) and non-callable (data) members.
        4. Signatures for all callable members.

        :param protocol: The Protocol class to wrap.
        """
        self._name: str = protocol.__name__
        self._annotations: dict[str, Any] = {
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
        """The name of the protocol class (ro)."""
        return self._name or ""

    @property
    def non_callable(self) -> set[str]:
        """Set of names of all non-method members (ro)."""
        return self._non_callable or set()

    @property
    def callable(self) -> set[str]:
        """Set of names of all method members (ro)."""
        return self._callable or set()

    @property
    def annotations(self) -> dict[str, Any]:
        """Dictionary of member names and their stringified type hints (ro)."""
        return self._annotations or {}

    @property
    def attributes(self) -> set[str]:
        """Set of all member names required by the protocol (ro)."""
        return self._attributes or set()

    @property
    def signatures(self) -> dict[str, str]:
        """Dictionary mapping method names to their full call signatures (ro)."""
        return self._signatures or {}

class FtwMethFuncWrap:
    """
    A metadata wrapper for callables (functions and methods).

    This class inspects a given callable to determine its nature (function vs.
    method) and extracts its signature and qualified name. It provides a
    consistent string representation that is particularly useful for
    generating error messages or documentation.

    Attributes:
        _len (int): Internal flag indicating if the wrapper is empty (0) or populated (1).
        _signature (Signature): The inspect.Signature object of the callable.
        _name (str): The qualified name (__qualname__) of the callable.
        _is_methode (bool): True if the callable is identified as a method.
        _is_function (bool): True if the callable is identified as a pure function.
    """
    def __init__(self, meth_func: Callable | None = None) -> None:
        """
        Initializes the wrapper and introspects the provided callable.

        The inspector handles edge cases where methods might be identified
        as functions by checking for dots in the qualified name.

        :param meth_func: The function or method to wrap.
        """
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
        """True if the wrapped object is a method (ro)."""
        return self._is_methode

    @property
    def is_function(self) -> bool:
        """True if the wrapped object is a function (ro)."""
        return self._is_function

    @property
    def is_empty(self) -> bool:
        """True if no callable was provided during initialization (ro)."""
        return self._len <= 0

    @property
    def name(self) -> str:
        """The qualified name of the callable (ro)."""
        return self._name

    def __len__(self) -> int:
        """Returns 1 if a callable is wrapped, 0 otherwise."""
        return self._len

    def __str__(self) -> str:
        """
        Returns a formatted string of the callable including its name and signature.

        For methods, it ensures that 'self' is visible in the signature string
        to accurately represent class-bound callables.
        """
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

class FtwProtocolError(FtwError):
    """
    Exception raised when an object violates one or more required Protocols.

    This error is specifically designed to work with the FtwProtocolWrap and
    FtwMethFuncWrap utilities. It captures the context of the failure—including
    the target function, the invalid argument, and the expected protocols—to
    generate a highly detailed cryptographic-style error message.

    **Inheritance Hierarchy**
    * :py:class:`FtwProtocolError`
    * :py:class:`FtwError`
    * :py:class:`FtwException`
    * :py:class:`Exception`

    Attributes:
        _meth_func (Callable): The function or method where the protocol violation occurred.
        _arg_name (str): The name of the argument that failed the check.
        _protocols (tuple): A collection of Protocol classes that were expected.
    """

    def __init__(self, meth_func: Callable, arg_name: str, protocols: tuple) -> None:
        """
        Initializes the error with the context of the protocol violation.

        :param meth_func: The callable that triggered the error.
        :param arg_name: The specific argument name that is non-compliant.
        :param protocols: The expected protocol(s) as a tuple.
        """
        super().__init__()
        self._meth_func: Callable = meth_func
        self._arg_name: str = arg_name
        self._protocols: tuple = protocols

    def __str__(self) -> str:
        """
        Returns a detailed, multi-line error message.

        The message is generated dynamically via `protocol_error_message`,
        listing all missing methods, attributes, and their required signatures.
        """
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
