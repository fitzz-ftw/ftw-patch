:orphan:

Getting Started with TestHomeEnvironment
========================================

The ``TestHomeEnvironment`` is designed to create a safe, isolated sandbox for 
testing tools that interact with the user's home directory and configuration 
paths.

Setup the Environment
---------------------

First, we need to define a base directory for our test. In this example, 
we use a directory within our documentation structure.

.. code:: python

    >>> from pathlib import Path
    >>> from ftw.develtool.testinfra import TestHomeEnvironment
    
    >>> # Define the anchor for our test environment
    >>> base_path = Path("doc/source/devel/testhome")
    >>> env = TestHomeEnvironment(base_path)
    >>> env.setup()

Understanding the Paths
-----------------------

After calling ``setup()``, the environment has prepared three main areas. 
Notice that the current working directory has automatically shifted to 
the ``output_dir``.

.. code:: python

    >>> # The current working directory is now the sandbox output
    >>> Path.cwd() == env.output_dir
    True
    
    >>> # The 'testinput' directory is meant for static files from Git
    >>> env.input_dir.name
    'testinput'

Isolation from the System
-------------------------

The environment has redirected the ``HOME`` variable. Libraries like 
``platformdirs`` will now point into our ``base_path`` instead of your 
real user folder.

.. code:: python

    >>> import os
    >>> os.environ['HOME'] == str(env.base_dir)
    True

Using the intuitive HOME alias

.. code:: python

    >>> env.HOME == env.base_dir
    True

Deploying Configuration Files
-----------------------------

You can easily "inject" files from your static ``testinput`` into the 
simulated user configuration. Imagine you have a file named ``config_v1.toml`` 
in your ``testinput`` folder.

*(Note: For this test to run, the file must exist in the real filesystem)*

.. code:: python

    >>> # This copies: testhome/testinput/config_v1.toml 
    >>> # to: testhome/.config/ftw/patch.toml (on Linux)
    >>> # target_path = env.copy2config("ftw", "config_v1.toml", "patch.toml")

Cleaning up
-----------

At the end of the doctest, we restore the original system state.

.. code:: python

    >>> env.teardown()
    >>> # CWD and Environment variables are now back to original values
