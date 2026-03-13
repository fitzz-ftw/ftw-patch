Global Color Management
=======================

The ``static`` module provides a centralized ``colors`` instance to manage terminal 
output consistently across the entire ``ftw-patch`` project.

Basic Usage
-----------

You can access colors either as direct properties or by using their string keys.
The latter is particularly useful for mixins or dynamic color assignments.

.. code-block:: python

   >>> from fitzzftw.patch.static import colors
   >>> colors.switch_to_testmode()

Direct property access

.. code-block:: python
    
   >>> print(f"{colors.RED}Error!{colors.RESET}")
   red>Error!<reset

Dictionary-like access

.. code-block:: python

   >>> print(f"{colors['YELLOW']}Warning!{colors.RESET}")
   ylw>Warning!<reset

Output Modes
------------

The ``colors`` manager supports different modes to adapt to various environments 
(e.g., CI/CD pipelines or log files).

* **NORMAL**: Standard ANSI escape sequences (Default).
* **PLAIN**: Returns empty strings (strips all formatting).
* **TEST**: Returns semantic tags (e.g., ``red>``) for easy assertion in tests.

.. code-block:: python

   # Switch to PLAIN mode for clean logs
.. code-block:: python

    >>> colors.mode = "PLAIN"
    >>> colors.RED == ""
    True

    >>> color = colors.get("green")
    >>> color == ""
    True

   # Switch to TEST mode for unit testing
.. code-block:: python

    >>> colors.mode = "TEST"
    >>> print(colors.CYAN)
    cyn>

    >>> colors.GREEN
    'grn>'

    >>> colors.YELLOW
    'ylw>'

    >>> colors.BOLD
    'bold.'

Validation and Type Safety
--------------------------

The system is strictly validated. Attempting to set an invalid mode will 
raise a ``ValueError``.

.. code-block:: python
   
   >>> colors.mode = "INVALID"  
   Traceback (most recent call last):
       ...
   ValueError: Invalid mode 'INVALID'. Must be one of ('NORMAL', 'PLAIN', 'TEST')
