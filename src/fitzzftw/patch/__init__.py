# Copyright (C) 2025 Fitzz TeXnik Welt <FitzzTeXnikWelt@t-online.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# File: src/fitzzftw/patch/__init__.py
# Author: Fitzz TeXnik Welt
# Email: FitzzTeXnikWelt@t-online.de
# License: LGPLv2 or above
"""
:mod:`fitzzftw.patch`
=====================

This package provides high-level patching and introspection utilities for
Python Protocols and callables. It dynamically adapts to the Python runtime
to ensure consistent metadata extraction across versions.

Architecture:
-------------
The package uses a version-dispatching mechanism to handle significant
changes in Python's introspection capabilities:

* **Python 3.14+**: Leverages PEP 649 (Deferred Evaluation) and 'annotationlib'.
* **Python 3.12 - 3.13**: Uses standard 'inspect' and 'typing' hints.
* **Python 3.11**: Implements legacy workarounds for Protocol introspection.

Exported API:
-------------
The following classes are resolved dynamically based on :data:`sys.version_info`:

* :class:`~.current_312_313.FtwProtocolWrap`: Metadata extractor for structural types.
* :class:`~.current_312_313.FtwMethFuncWrap`: Signature and metadata wrapper for callables.

Note:
    Documentation is primarily linked to the :mod:`.current_312_313`
    implementation to provide a stable reference, though all versions
    adhere to the same public interface.
"""
