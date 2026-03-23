# File: src/fitzzftw/patch/exceptions.py
# Author: Fitzz TeXnik Welt
# Email: FitzzTeXnikWelt@t-online.de
# License: LGPLv2 or above
"""
:mod:`.exceptions`
===============================

This module provides a specialized hierarchy of exceptions for the fitzzftw framework.
It includes advanced introspection tools that adapt to the running Python version
to handle Protocols and callables.

Core Features:
--------------
* **Protocol Validation**:
  Uses :class:`~fitzzftw.patch.current_312_313.FtwProtocolWrap` and :class:`.FtwProtocolError` 
  to generate highly detailed error messages when objects do not match required interfaces.
* **Signature Inspection**:
  Employs :class:`fitzzftw.patch.current_312_313..FtwMethFuncWrap` to accurately represent
  methods and functions (including 'self' injection) in diagnostic outputs.
* **Type Awareness**:
  Automatically resolves type names and hints into human-readable
  strings for clearer debugging.

The primary goal of this module is to provide actionable implementation
guides for the developer by resolving version-specific introspection differences
(PEP 649/annotationlib vs. legacy typing).
"""
import sys
from collections.abc import Callable
from pathlib import Path

if sys.version_info < (3, 12): # pragma: no cover, only needed for python <=3.11
    from fitzzftw.patch.legacy_311 import FtwMethFuncWrap, FtwProtocolWrap
elif sys.version_info >= (3, 14):  # pragma: no cover, only needed for python >=3.14
    from fitzzftw.patch.future_314_ge import FtwMethFuncWrap, FtwProtocolWrap
else:  # pragma: no cover, only needed for python 3.12, 3.13
    from fitzzftw.patch.current_312_313 import FtwMethFuncWrap, FtwProtocolWrap

#SECTION - Helperfunctions and -classes


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
    # test_file = testfiles_dir / "exceptions_debug_314.rst"
    # test_file = testfiles_dir / "exceptions_debug_311.rst"
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
