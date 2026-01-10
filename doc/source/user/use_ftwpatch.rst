
.. _cli-reference:

Command Line Tool ftwpatch
=================================

..
 This section describes the CLI command :command:`ftwpatch` . For a practical 
 introduction, see the :ref:`ftw-patch-get-argparser-func` guide.

.. tip:: Why we recommend pipx
   :class: sd-card-text

   Unlike standard ``pip``, **pipx** ensures that the application's dependencies are kept strictly 
   separate from other tools. This makes it impossible to "break" your system Python or other 
   installed utilities.

.. include:: ./use_ftwpatch_pre.rst.inc
    :parser: rst


.. argparse::
   :module: ftw.patch.ftw_patch
   :func: _get_argparser
   :prog: ftwpatch



.. include:: ./use_ftwpatch_post.rst.inc
    :parser: rst
