Getting Started: Terminal Colors and Protocol Safety
=====================================================

The :mod:`.base` module provides the :class:`.base.TerminalColorMixin`, which allows any class to
print colorized output while ensuring structural integrity through protocols. 

.. CLASS -  TerminalColorMixin Class

Using the TerminalColorMixin Class
-----------------------------------

The :class:`~fitzzftw.patch.base.TerminalColorMixin` class provides standardized CLI color capabilities. 
It encapsulates ANSI escape sequences and ensures a safe fallback 
(plain text) for environments where colors are disabled or not supported.

Global Controls
~~~~~~~~~~~~~~~
Unlike some other tools, :class:`~fitzzftw.patch.base.TerminalColorMixin` does **not** perform "magic" 
terminal detection via :func:`~os.isatty`. This ensures consistent behavior 
across different environments and pipes.

The mixin features a global toggle to enable or disable colorized output 
entirely. This is particularly useful when piping output to logs, files, 
or other scripts that cannot process ANSI codes.

.. code-block:: python

    >>> from fitzzftw.patch.ftw_patch import TerminalColorMixin

By default, colors are enabled. To disable them globally:

.. code-block:: python

    >>> TerminalColorMixin.use_colors = False

The colors defined are the following. There is a special color called
*terminal*, this is the color of the terminal it is run from.

    >>> TerminalColorMixin._ANSI.defined_colors 
    ['red', 'green', 'yellow', 'cyan', 'terminal']



    >>> TerminalColorMixin._ANSI.defined_keys
    ['red', 'green', 'yellow', 'cyan', 'reset', 'bold', 'terminal']



Method Signature
~~~~~~~~~~~~~~~~

The :meth:`~fitzzftw.patch.base.TerminalColorMixin.colorize` method is the primary interface for styling text. 
It accepts a ``color_key`` (red, green, yellow, terminal, or cyan) and an optional ``bold`` flag.

Testing and Validation
~~~~~~~~~~~~~~~~~~~~~~

In automated testing environments like doctests, raw ANSI escape codes are 
invisible and difficult to assert. To solve this, the internal 
:attr:`~fitzzftw.patch.base.TerminalColorMixin._ANSI` 
mapping can be overridden with human-readable placeholders.

.. code-block:: python

    >>> # Mocking colors for readable test assertions

    >>> TerminalColorMixin._ANSI.switch_to_testmode()
    >>> TerminalColorMixin._ANSI.mode
    'TEST'

    >>> m = TerminalColorMixin()
    >>> m._ANSI.mode
    'TEST'

If :data:`~fitzzftw.patch.base.TerminalColorMixin.use_colors` is ``False``, 
the text remains plain:

.. code-block:: python

    >>> TerminalColorMixin.use_colors = False
    >>> m.colorize(text="Error", color_key="red", bold=True)
    Error

If :attr:`~fitzzftw.patch.base.TerminalColorMixin.use_colors` is set to ``True``, 
the mocked style is applied:

.. code-block:: python

    >>> TerminalColorMixin.use_colors = True
    >>> m.colorize("Error", "red", True)
    bold.red>Error<reset

Diagnostic Tool: color_terminal_check
-------------------------------------

Beyond the mixin, the module provides a diagnostic function to verify 
terminal compatibility. This function prints a visual test pattern 
to the console.

Standalone Usage:
~~~~~~~~~~~~~~~~~

If the package is installed, this diagnostic can be invoked directly 
from the command line:

.. code-block:: bash

    $ ftw-terminal-color-check

Programmatic Usage:
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from fitzzftw.patch.ftw_patch import color_terminal_check
    >>> color_terminal_check()
    =================================================
    ========== Visual Terminal Color Check ==========
    Enabled : grn>GRN<reset|bold.grn>GRN-B<reset|red>RED<reset|bold.red>RED-B<reset|cyn>CYN<reset|bold.cyn>CYN-B<reset|ylw>YLW<reset|bold.ylw>YLW-B<reset
    Disabled: GRN|GRN-B|RED|RED-B|CYN|CYN-B|YLW|YLW-B
    =================================================

.. !SECTION

Basic Integration
~~~~~~~~~~~~~~~~~

To equip a class with color capabilities, inherit from 
:class:`~fitzzftw.patch.base.TerminalColorMixin`. 
The :meth:`~fitzzftw.patch.base.TerminalColorMixin.colorize` method then 
becomes available to handle styled output.


.. code-block:: python

    >>> class PatchReporter(TerminalColorMixin):
    ...     def info(self, message: str):
    ...         self.colorize(message, "cyan", bold=True)

    >>> reporter = PatchReporter()
    >>> reporter.info("Starting patch process...")
    bold.cyn>Starting patch process...<reset

The :meth:`~.base.TerminalColoMixin.print` method is more advanced: it requires the object to be 
:class:`.protocol.LineLike` 
(it must have a ``_color_map``, ``prefix`` and ``orig_line`` attribute). 

If we try to print an object that does not follow this protocol, the framework 
raises a detailed :exc:`~.exceptions.FtwProtocolError`. Doctest allows us to verify 
this behavior by looking for the specific error message:

    >>> reporter.print() # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS  +REPORT_NDIFF
    Traceback (most recent call last):
      ...
    fitzzftw.patch.exceptions.FtwProtocolError:
    Error: TerminalColorMixin.print for PatchReporter
    Please implement:
      LineLike:
        Args:
          _color_map: dict
          orig_line: str
          prefix: str | None
    or
      overwrite TerminalColorMixin.print(self, **kwargs) -> None.

Let's create a class which fullfils the :class:`.lines.LineLike`` protocols. 

    >>> class PatchLineReporter(TerminalColorMixin):
    ...     _color_map = {"?": "green", "": "yellow"}
    ...     def __init__(self):
    ...         self.prefix: str = "?"
    ...         self.orig_line:str = "Hallo world."

    >>> line = PatchLineReporter()


    >>> from fitzzftw.patch.base import LineLike
    
    >>> isinstance(line, LineLike)
    True

    >>> line.print()
    grn>Hallo world.<reset

    >>> line.prefix=""
    >>> line.orig_line="Have a nice day."
    >>> line.print()
    ylw>Have a nice day.<reset

    >>> line.prefix="&"
    >>> line.orig_line="Have a nice day."
    >>> line.print()
    trm>Have a nice day.<reset
