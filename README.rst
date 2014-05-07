Cuckoo Drive
------------
.. image:: https://travis-ci.org/lukasmartinelli/cuckoodrive.svg?branch=master
  :target: https://travis-ci.org/lukasmartinelli/cuckoodrive
.. image:: https://coveralls.io/repos/lukasmartinelli/cuckoodrive/badge.png?branch=master
  :target: https://coveralls.io/r/lukasmartinelli/cuckoodrive?branch=master
.. image:: https://landscape.io/github/lukasmartinelli/cuckoodrive/master/landscape.png
  :target: https://landscape.io/github/lukasmartinelli/cuckoodrive/master
Aggregates all the free space provided on various cloud storage providers into one big drive.

Install
------------------

1. ``git clone https://github.com/lukasmartinelli/cuckoodrive.git && cd cuckoodrive``
2. ``python setup.py install``

Use
------------------

Synchronize the current folder with CuckooDrive consisting out of two local folders::

    cuckoodrive sync --remotes /tmp/fs1 /tmp/fs2


Development
-----------
CuckooDrive is written for CPython 2.7 because this is the version `PyFilesystem <http://www.python.org/>`_. works best. Nonetheless we try to write Python that is compatible with Python 3.4 and PyPy as well.

Setup Environment::

    python setup.py develop

Run the unit tests::

    python setup.py test
