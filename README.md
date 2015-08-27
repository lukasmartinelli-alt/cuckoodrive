# Cuckoo Drive [![Travis](https://travis-ci.org/lukasmartinelli/cuckoodrive.svg?branch=master)](https://travis-ci.org/lukasmartinelli/cuckoodrive) [![](https://img.shields.io/coveralls/lukasmartinelli/cuckoodrive.svg)](https://coveralls.io/r/lukasmartinelli/cuckoodrive?branch=master)

Aggregates all the free space provided on various cloud storage
providers into one big drive.

## Support

**This project has been discontinued because [I don’t want to write
another distributed filesystem.**

http://lukasmartinelli.ch/idea/2014/07/03/future-of-cuckoodrive.html)

## Concept

http://lukasmartinelli.ch/idea/2014/03/11/using-the-cloud-storages-as-one-big-encrypted-disk.html

![Idea Overview](http://lukasmartinelli.ch/media/cuckoodrive_concept.png)

## Concept

http://lukasmartinelli.ch/python/2014/03/13/cuckoo-drive-architecture.html

![Implementation Overview](http://lukasmartinelli.ch/media/cuckoo_drive_implementation.png)

## Install

1.  `git clone https://github.com/lukasmartinelli/cuckoodrive.git && cd cuckoodrive`
2.  `python setup.py install`

## Use

Synchronize the current folder with CuckooDrive consisting out of two
local folders:

```bash
cuckoodrive sync --remotes /tmp/fs1 /tmp/fs2
```

## Development

CuckooDrive is written for CPython 2.7 because this is the version
PyFilesystem. works best.

Setup the environment.

```bash
python setup.py develop
```

Run the unit tests.

```bash
python setup.py test
```
