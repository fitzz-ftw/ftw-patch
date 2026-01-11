:orphan:


Getting Started: FTW Converter Functions
=========================================

The :py:mod:`fitzzftw.baselib.converter` module provides utility functions to transform 
various data types into a standardized format. This is particularly useful 
for processing configuration files and command-line arguments.



Boolean Conversion
------------------

The :py:func:`str2bool` function is the core utility of this module. It interprets 
string representations of boolean values, which are common in TOML files 
or CLI inputs.

1. Successful Conversions
~~~~~~~~~~~~~~~~~~~~~~~~~

The function is case-insensitive and handles multiple truthy and falsy strings.

.. code:: python

    >>> from fitzzftw.baselib.converter import str2bool
    
Truthy values
^^^^^^^^^^^^^^

.. code:: python

    >>> str2bool("true")
    True
    >>> str2bool("YES")
    True
    >>> str2bool("1")
    True
    >>> str2bool("on")
    True

Falsy values
^^^^^^^^^^^^

.. code:: python

    >>> str2bool("false")
    False
    >>> str2bool("no")
    False
    >>> str2bool("0")
    False
    >>> str2bool("off")
    False

2. Handling Native Boolean Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the value is already a boolean, the function returns it unchanged. 
This is useful when the source might already be parsed (e.g., from a 
TOML library).

.. code:: python

    >>> str2bool(True)
    True
    >>> str2bool(False)
    False

3. Error Handling and Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a value does not match any known boolean representation, the function 
raises a :py:class:`ValueError`. This follows our strategy of specific error reporting.

.. code:: python

    >>> str2bool("unknown_value")
    Traceback (most recent call last):
        ...
    ValueError: Cannot convert 'unknown_value' to boolean.

