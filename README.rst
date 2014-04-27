Cuckoo Drive
------------
.. image:: https://travis-ci.org/lukasmartinelli/cuckoodrive.svg?branch=master
  :target: https://travis-ci.org/lukasmartinelli/cuckoodrive
.. image:: https://coveralls.io/repos/lukasmartinelli/cuckoodrive/badge.png?branch=master
  :target: https://coveralls.io/r/lukasmartinelli/cuckoodrive?branch=master
.. image:: https://landscape.io/github/lukasmartinelli/cuckoodrive/master/landscape.png
  :target: https://landscape.io/github/lukasmartinelli/cuckoodrive/master
Aggregates all the free space provided on various cloud storage providers into one big drive.

Development
-----------
The test suite depends on ``tox`` to test all the supported Python versions::

    pip install tox pytest

Setup Environment:

1. clone repository
2. ``pip install tox``
3. ``pip install -e .``

Run the tests for all supported Python versions::

    tox

Run the tests for a specific Python version (e.g. Python 2.7)::

    tox -e py27
