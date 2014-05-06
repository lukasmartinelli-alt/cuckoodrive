Cuckoo Drive
------------
.. image:: https://travis-ci.org/lukasmartinelli/cuckoodrive.svg?branch=master
  :target: https://travis-ci.org/lukasmartinelli/cuckoodrive
.. image:: https://coveralls.io/repos/lukasmartinelli/cuckoodrive/badge.png?branch=master
  :target: https://coveralls.io/r/lukasmartinelli/cuckoodrive?branch=master
.. image:: https://landscape.io/github/lukasmartinelli/cuckoodrive/master/landscape.png
  :target: https://landscape.io/github/lukasmartinelli/cuckoodrive/master
Aggregates all the free space provided on various cloud storage providers into one big drive.

Compability Matrix
------------------
CuckooDrive is tested against all major Platforms.
The current FUSE implementation doesn't play well with Python 3.

=============   =====  ======  ======
Platform        py27   py34    pypy
=============   =====  ======  ======
Unix (FUSE)     Yes    No      Yes
OSX (OSXFUSE)   Yes    Yes     Yes
Win (Dokan)     Yes    Yes     Yes
=============   =====  ======  ======


Development
-----------
CuckooDrive is written for CPython 2.7 because this is the version `PyFilesystem <http://www.python.org/>`_. works best. Nonetheless we try to write Python that is compatible with Python 3.4 and PyPy as well.

Setup Environment:

1. clone repository
2. setup virtual environment
3. ``python setup.py develop``

Run the unit tests::

    python setup.py test
