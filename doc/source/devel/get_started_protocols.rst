Get Started with Ftw Patch Protocols Module
=============================================

The :mod:`.protocols` module defines the structural interfaces of the framework. 
Instead of rigid inheritance, we use :class:`~python:typing.Protocol` to 
implement "Duck Typing". This ensures that different components can work 
together as long as they provide the required attributes and methodes.

The LineLike Protocol
----------------------

The most important protocol is :class:`.protocols.LineLike`. It defines what 
an object must look like to be processed by the framework's output systems, 
such as the :class:`.base.TerminalColorMixin`.

An object satisfies this protocol if it has these three attributes:

1. ``_color_map``: A dictionary mapping prefix strings to color keys.
2. ``prefix``: A string (or ``None``) used as the **index** for the map.
3. ``orig_line``: The actual text content of the line.

Let's verify this with a test:

    >>> from fitzzftw.patch.protocols import LineLike
    >>> from fitzzftw.patch.base import TerminalColorMixin

We can create a simple class that implements the required structure:

    >>> class MySimpleLine:
    ...     def __init__(self, text):
    ...         self._color_map = {"!": "red"}
    ...         self.prefix = "!"
    ...         self.orig_line = text

Since :class:`LineLike` is decorated with :func:`~python:typing.runtime_checkable`, 
we can use :func:`isinstance` to verify the implementation:

    >>> simple_line = MySimpleLine("Danger!")
    >>> isinstance(simple_line, LineLike)
    True

Configuration Protocols
-----------------------

The framework also uses protocols to handle configuration options. This makes 
it easy to swap different option sources (like CLI arguments or config files).

* :class:`.protocols.BackupOptions`: 
    Handles settings for file backups and extensions.
* :class:`.protocols.WhitespaceOptions`: 
    Defines rules for whitespace normalization.
* :class:`.protocols.ArgParsOptions`: 
    A master protocol that combines all available application options.

These protocols are mainly used for static type checking to ensure that 
functions receive exactly the settings they need.
