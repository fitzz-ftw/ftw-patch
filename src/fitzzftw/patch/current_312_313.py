# File: src/fitzzftw/patch/current_312_313.py
# Author: Fitzz TeXnik Welt
# Email: FitzzTeXnikWelt@t-online.de
# License: LGPLv2 or above
"""
Version-Specific Protocol Introspection (Python 3.12 - 3.13)
=============================================================

This module implements the metadata extraction for Python Protocols using
the standard library features available in Python 3.12 and 3.13.

It defines the :class:`FtwProtocolWrap` and :class:`FtwSignatureWrap` classes,
which utilize :func:`typing.get_type_hints` and :mod:`inspect` to resolve
structural requirements and method signatures for documentation purposes.

Note:
    For Python 3.11, use :mod:`.legacy_311`. 
    For Python 3.14+, use :mod:`.future_314_ge`.
    
"""
from collections.abc import Callable
from inspect import Signature, isfunction, ismethod, signature
from pathlib import Path
from typing import Any, get_type_hints

from fitzzftw.patch.utils import get_string_of_type


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
            self._name: str = ""
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


if __name__ == "__main__": # pragma: no cover
    from doctest import FAIL_FAST, testfile
    
    be_verbose = False
    be_verbose = True
    option_flags = 0
    option_flags = FAIL_FAST
    test_sum = 0
    test_failed = 0
    
    # Pfad zu den dokumentierenden Tests
    testfiles_dir = Path(__file__).parents[3] / "doc/source/devel"
    test_file = testfiles_dir / "get_started_current_312_313.rst"
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
