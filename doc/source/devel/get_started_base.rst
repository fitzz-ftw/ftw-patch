.. SECTION - 

ColorMixin Class
----------------

The :class:`~fitzzftw.patch.ftw_patch.ColorMixin` class provides standardized CLI color capabilities. 
It encapsulates ANSI escape sequences and ensures a safe fallback 
(plain text) for environments where colors are disabled or not supported.

Global Controls
~~~~~~~~~~~~~~~
Unlike some other tools, :class:`~fitzzftw.patch.ftw_patch.ColorMixin` does **not** perform "magic" 
terminal detection via :func:`~os.isatty`. This ensures consistent behavior 
across different environments and pipes.

The mixin features a global toggle to enable or disable colorized output 
entirely. This is particularly useful when piping output to logs, files, 
or other scripts that cannot process ANSI codes.

.. code-block:: python

    >>> from fitzzftw.patch.ftw_patch import ColorMixin

By default, colors are enabled. To disable them globally:

.. code-block:: python

    >>> ColorMixin.use_colors = False
    >>> ColorMixin._ANSI.defined_colors 
    ['red', 'green', 'yellow', 'cyan']

Basic Integration
~~~~~~~~~~~~~~~~~

To equip a class with color capabilities, inherit from :class:`~fitzzftw.patch.ftw_patch.ColorMixin`. 
The :meth:`~fitzzftw.patch.ftw_patch.ColorMixin.colorize` method then becomes available to handle styled output.

.. code-block:: python

    >>> class PatchReporter(ColorMixin):
    ...     def info(self, message: str):
    ...         formatted = self.colorize(message, "cyan", bold=True)
    ...         print(formatted)

    >>> reporter = PatchReporter()
    >>> reporter.info("Starting patch process...")
    Starting patch process...

Method Signature
~~~~~~~~~~~~~~~~

The :meth:`~fitzzftw.patch.ftw_patch.ColorMixin.colorize` method is the primary interface for styling text. 
It accepts a ``color_key`` (red, green, or cyan) and an optional ``bold`` flag.

Testing and Validation
~~~~~~~~~~~~~~~~~~~~~~

In automated testing environments like doctests, raw ANSI escape codes are 
invisible and difficult to assert. To solve this, the internal :attr:`~fitzzftw.patch.ftw_patch.ColorMixin._ANSI` 
mapping can be overridden with human-readable placeholders.

.. code-block:: python

    >>> # Mocking colors for readable test assertions

    >>> ColorMixin._ANSI.switch_to_testmode()
    >>> ColorMixin._ANSI.mode
    'TEST'

    >>> m = ColorMixin()
    >>> m._ANSI.mode
    'TEST'

If :data:`~fitzzftw.patch.ftw_patch.ColorMixin.use_colors` is ``False``, the text remains plain:

.. code-block:: python

    >>> ColorMixin.use_colors = False
    >>> m.colorize(text="Error", color_key="red", bold=True)
    'Error'

If :attr:`~fitzzftw.patch.ftw_patch.ColorMixin.use_colors` is set to ``True``, the mocked style is applied:

.. code-block:: python

    >>> ColorMixin.use_colors = True
    >>> m.colorize("Error", "red", True)
    'bold.red>Error<reset'

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
