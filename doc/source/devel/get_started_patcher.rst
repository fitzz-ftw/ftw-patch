.. SECTION - Statistics
Get Started with PatchStatistics
================================

>>> from fitzzftw.patch.static import colors
>>> colors.switch_to_testmode(False)


The :class:`.patcher.PatchStatistics` class is responsible for collecting 
information during the patching process and presenting it to the user.

Initialization and Properties
-----------------------------

When you create a new instance, you define the verbosity level. All counters 
start at zero:

>>> from fitzzftw.patch.patcher import PatchStatistics
>>> stats = PatchStatistics()

You can access the current state through several read-only properties:

>>> stats
PatchStatistics(verbosity: 0)

>>> stats.verbosity
0

>>> stats.total_files
0

>>> stats.lines_added
0
>>> stats.lines_removed
0

>>> stats.files_modified
0

>>> stats.files_created
0

>>> stats.files_deleted
0

Basic Output
------------

The :meth:`.PatchStatistics.print` method generates a summary based on the gathered data. 
Even without any files added, it provides a basic status report:

>>> stats.print() 
Files processed: 0

Higher Verbosity
----------------

Changing the verbosity level doesn't affect the data, but it will change 
what :meth:`~.PatchStatistics.print` eventually shows (once data is present). 


>>> stat1 = PatchStatistics(verbosity=1)
>>> stat1
PatchStatistics(verbosity: 1)

>>> stat1.print()
Files processed: 0
Lines processed: 0


.. !SECTION - Statistics

>>> stat_error = PatchStatistics()

>>> from fitzzftw.patch.lines import HeadLine
>>> from fitzzftw.patch.container import DiffCodeFile
>>> h1 = HeadLine("--- a/test.py")
>>> diff_error = DiffCodeFile(h1)

>>> stat_error.add_file(diff_error)
Traceback (most recent call last):
    ...
fitzzftw.patch.exceptions.FtwPatchError: New Header not found!



FtwPatch Class
=================

The :py:class:`.patcher.FtwPatch` class is the high-level controller 
of the module. It coordinates the parsing of the patch file and the application 
of changes to the target directory using a safe staging mechanism.

.. SECTION - SetUp

.. _ftw-patch-setup-env:


.. dropdown:: Environment Setup and Path Initialization for the Tests
    :chevron: down-up
    :color: info

    .. code:: python

        >>> from pathlib import Path
        >>> from fitzzftw.develtool.testinfra import TestHomeEnvironment


        >>> env = TestHomeEnvironment(Path("doc/source/devel/testhome"))
        >>> env.setup()
        >>> env.input_readonly = True
        >>> env.do_not_clean = False

.. !SECTION


.. CLASS - FtwPatch


Initialization and Properties
------------------------------


.. code:: python

    >>> from fitzzftw.patch.ftw_patch import FtwPatch
    >>> from argparse import Namespace



1. Preparation and Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To initialize the patcher, we provide an :obj:`options` object which fullfill the 
:class:`~.protocols.ArgParsOptions` protocol,
containing all necessary settings.



We use the dummy_patch_file created in the setup

.. code:: python

    >>> Path("patch.diff").touch()
    >>> options = Namespace(
    ...     patch_file=Path("patch.diff"),
    ...     target_directory=Path("."),
    ...     strip_count=0,
    ...     normalize_whitespace=False,
    ...     ignore_blank_lines=False,
    ...     ignore_all_whitespace=False,
    ...     dry_run=False,
    ...     verbose=0
    ... )
    >>> patcher = FtwPatch(options)
    >>> patcher # doctest: +ELLIPSIS
    FtwPatch(patch_file=...('patch.diff'))

2. Executing the Patch (:py:meth:`.FtwPatch.apply` method)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:meth:`~.FtwPatch.apply` method executes the patching logic. It returns ``0`` 
if the process was successful.

Using the options defined above

.. code:: python

    >>> patcher.apply(options)

Verifying Dry-Run Behavior
---------------------------

A key feature of :py:class:`~.patcher.FtwPatch` is the ability to simulate changes. 
When ``options.dry_run`` is set to ``True``, the internal staging area is 
prepared, but no changes are written back to the target files.

Create a test file

.. code:: python

    >>> test_file = env.copy2cwd("hello.py")

    >>> test_file = Path("hello.py")
    >>> test_file.write_text("print('Old')\n")
    13
    
Define a patch for this file

.. code:: python

    >>> _ =env.copy2cwd("hello.patch", "test.patch")

Set up dry_run

.. code:: python

    >>> options.patch_file = Path("test.patch")
    >>> options.dry_run = True
    >>> simulation = FtwPatch(options)
    >>> simulation.apply(options)
    
    
The file remains unchanged

.. code:: python

    >>> test_file.read_text()
    "print('Old')\n"




Inspecting Patcher Properties
-----------------------------

Once initialized, the :py:class:`~.patcher.FtwPatch` instance provides read-only 
access to its configuration and the results of the parsing process 
through various properties.

Basic paths used by the patcher:

Accessing the core paths

.. code:: python

    >>> patcher.patch_file_path.name
    'test.patch'
    >>> patcher.target_directory.as_posix()
    '.'

.. _ftw_patch-ftw_patch-strip_count-property:

:py:attr:`~.patcher.FtwPatch.strip_count`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :py:attr:`~.patcher.FtwPatch.strip_count` property returns the number of leading path components 
that are stripped from the file names found in the patch file **(ro)**.

Accessing the strip count configuration

.. code:: python

    >>> patcher.strip_count
    0

The patcher also exposes the normalization settings derived from the options:

.. code:: python

    >>> patcher.normalize_whitespace
    False
    >>> patcher.ignore_blank_lines
    False
    >>> patcher.ignore_all_whitespace
    False




Accessing Parsed Data
~~~~~~~~~~~~~~~~~~~~~~~~

The :py:attr:`~.FtwPatch.parsed_files` property provides access to the structured data 
before or after the patch is applied. This is useful for generating 
reports or verifying the patch content programmatically.

In our previous setup, we used a patch with one file: 'hello.py'


.. code:: python

    >>> len(simulation.parsed_files)
    1
    >>> diff_file = simulation.parsed_files[0]
    >>> diff_file.orig_header.content
    'hello.py'
    >>> len(diff_file.hunks)
    1

Verbosity and Logging
~~~~~~~~~~~~~~~~~~~~~~~~

The verbosity level determines how much information is printed to the 
console during the execution of the :py:meth:`~.patcher.FtwPatch.apply` method.

.. code:: python

    >>> patcher.verbose
    0

Inspecting the Patcher
~~~~~~~~~~~~~~~~~~~~~~

You can check the current configuration of an :py:class:`~.patcher.FtwPatch` instance through 
its read-only properties **(ro)**.

Check the configuration via properties

.. code:: python

    >>> patcher = FtwPatch(options)
    >>> patcher.dry_run
    True
    >>> patcher.verbose
    0

Verify paths are handled correctly

.. code:: python

    >>> isinstance(patcher.patch_file_path, Path)
    True

Advanced Configuration
-----------------------

The patcher can handle different whitespace styles. This is useful when 
dealing with files from different operating systems. Enabling these 
options changes how the patch is parsed.

Enable whitespace normalization

.. code:: python

    >>> options.normalize_whitespace = True
    >>> advanced_patcher = FtwPatch(options)

The patcher now uses advanced parsing logic

.. code:: python

    >>> advanced_patcher.apply(options)

Simulation vs. Real Execution
------------------------------

The :py:meth:`~.patcher.FtwPatch.apply` method is a procedure that performs the patching process. 
You can switch between a safe simulation and the actual write process.


1. Simulation Mode (Safety first)

.. code:: python

    >>> options.dry_run = True
    >>> simulation = FtwPatch(options)
    >>> simulation.apply(options)

2. Real Application (Default behavior)

.. code:: python

    >>> options.dry_run = False
    >>> real_patcher = FtwPatch(options)

This executes the final commit to the file system

.. code:: python

    >>> real_patcher.apply(options)


.. _ftw_patch-ftw_patch-apply-backup_logic:

:py:meth:`.FtwPatch.apply`
--------------------------

When applying changes, the patcher automatically creates backups of the 
modified files. If no specific backup directory is provided, the backup 
is created in the same directory as the original file using an extension.

.. code:: python

    >>> options.backup_ext = '.bak'
    >>> options.backup=True
    >>> options # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    Namespace(patch_file=...Path('test.patch'), 
        target_directory=...Path('.'), 
        strip_count=0, 
        normalize_whitespace=True, 
        ignore_blank_lines=False, 
        ignore_all_whitespace=False, 
        dry_run=False, 
        verbose=0, 
        backup_ext='.bak',
        backup=True)
    
.. code:: python

    >>> Path('hello.py').read_text()
    "print('New')\n"

Handling Patch Failures (Safety First)
--------------------------------------

A key feature of :py:class:`~.patcher.FtwPatch` is its integrity check. If the context of a 
patch (a "hunk") does not exactly match the target file, the process 
aborts immediately. 

This prevents the tool from applying changes to the wrong lines, ensuring 
your source code remains consistent.    

.. code:: python

    >>> patcher.apply(options) # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    Traceback (most recent call last):
        ...
    fitzzftw.patch.exceptions.PatchParseError: Hunk mismatch at line 1. 
    ... not match the hunk's context.

Verification of Atomicity
--------------------------

Because the patch failed the integrity check, no changes were written to 
the disk, and no backup file was created. The operation is atomic.

The backup should NOT exist because nothing was changed

.. code:: python

    >>> backup_file = Path("hello.py.bak")
    >>> backup_file.exists()
    False

The original file remains untouched

.. code:: python

    >>> orig_file = Path(patcher._patch_files[0].orig_header.content)
    >>> orig_file.read_text()
    "print('New')\n"


Error Handling
--------------

The :py:class:`~.patcher.FtwPatch` class ensures data integrity. If a patch is malformed 
or files are missing, it raises an exception to prevent partial changes.

Triggering an error with a missing file

.. code:: python

    >>> options.patch_file = Path("missing.patch")
    >>> FtwPatch(options).apply(options) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    FileNotFoundError: Patch file not found at ...Path('missing.patch')


Full Cycle: Patching a Python Source File
-----------------------------------------

To demonstrate the full power of :py:meth:`.FtwPatch.apply`, we will perform a complete 
patching cycle: creating a source file, defining a unified diff, and applying it.

1. **Setup the Source File**
   We create a simple Python file with a few lines of code.

.. code:: python
    >>> env.clean_home()
    >>> source_path = env.copy2cwd("app.py")
    >>> deleted_path = env.copy2cwd("app_old_config.py", "old_config.py")

2. **Create the Patch File**
   We define a patch that changes the greeting and adds a new function. 
   Notice the use of standard Unified Diff prefixes.

.. code:: python

    >>> patch_path = env.copy2cwd("changes_multi.diff","changes.diff")

.. "changes_multi.diff",

3. **Apply the Patch**
   Now we use :class:`~.patcher.FtwPatch` to apply these changes. We will enable backup 
   generation to see the safety mechanism in action.

.. code:: python

    >>> from argparse import Namespace
    >>> run_options = Namespace(
    ...     patch_file=patch_path,
    ...     target_directory=Path("."),
    ...     strip_count=1,
    ...     normalize_whitespace=False,
    ...     ignore_blank_lines=False,
    ...     ignore_all_whitespace=False,
    ...     dry_run=False,
    ...     verbose=1,
    ...     backup=True,
    ...     backup_ext=".orig"
    ... )
    >>> patcher = FtwPatch(run_options)
    >>> patcher.apply(run_options)
    
    Traceback (most recent call last):
        ...
    fitzzftw.patch.exceptions.PatchParseError: Hunk starting at line 0 exceeds file bounds. File has 0 lines.

4. **Verify the Results**
   The original file should now contain the new content, and a backup 
   file :file:`app.py.orig` should exist.

.. code:: python

    >>> print(source_path.read_text())
    def greet():
        print('Hello World')
    <BLANKLINE>
    def farewell():
        print('Goodbye')
    <BLANKLINE>
    if __name__ == '__main__':
        greet()
    <BLANKLINE>

    >>> Path("app.py.orig").exists()
    True
    >>> "print('Hello')" in Path("app.py.orig").read_text()
    True

Copy the patched file to a persistant directory.

    >>> _ = env.cwd2doc_inc("app.py")

.. dropdown:: Before and After
    :chevron: down-up
    :color: info

    .. grid:: 2
        :gutter: 3

        .. grid-item-card:: Original Files (Input)
            :class-header: bg-light
            :shadow: md

            .. literalinclude:: testhome/testinput/app.py
                :language: python
                :linenos:
                :caption: app.py (original)

            .. literalinclude:: testhome/testinput/changes.diff
                :language: diff
                :caption: changes.diff

        .. grid-item-card:: Patched File (Output)
            :class-header: bg-success text-white
            :shadow: md

            .. literalinclude:: testhome/testdocinc/app.py
                :language: python
                :linenos:
                :emphasize-lines: 2, 4-6
                :caption: app.py (patched)

    >>> Path("old_config.py.orig").exists()
    True

    >>> deleted_path.exists()
    False

    >>> Path("utils.py").exists()
    True

    >>> Path("utils.py.orig").exists()
    False


    >>> for diff_ in patcher.parsed_files:
    ...     stats.add_file(diff_)
    ...     stat1.add_file(diff_)

    >>> stats.print()
    Files processed: 3

    >>> stat1.print()
    Files processed: 3
    Lines processed: 11

    >>> stats.lines_added
    7

    >>> stats.lines_removed
    4


    >>> stats.files_modified
    1

    >>> stats.files_created
    1

    >>> stats.files_deleted
    1


.. !CLASS
.. SECTION - CleanUp

.. dropdown:: Cleanup Testenvironment
    :chevron: down-up
    :color: info


    .. code:: python

        >>> env.input_readonly=False
        
        >>> env.do_not_clean = False

        >>> env.teardown()
        
        >>> env.clean_home()

.. !SECTION
