from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

tests_require = [
    'pytest',
    'pytest-cache',
    'pytest-cov',
    'mock',
]

install_requires = [
    'fs',
    'pyfs-dropbox',
    'docopt',
    'pyinotify',
    'blessings'
]

dependency_links= [
    'https://github.com/lukasmartinelli/fs-dropbox/tarball/master#egg=pyfs-dropbox-0.3.3',
]


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name="cuckoodrive",
    version="0.0.1",
    author="Lukas Martinelli",
    author_email="me@lukasmartinelli.ch",
    url="https://github.com/lukasmartinelli/cuckoodrive",
    description=("Aggregates all the free space provided on various \
                 cloud storage providers into one big drive."),
    long_description=open('README.rst').read(),
    packages=['cuckoodrive'],
    install_requires=install_requires,
    extras_require={
        'test': tests_require
    },
    tests_require=tests_require,
    dependency_links=dependency_links,
    cmdclass={'test': PyTest},
    license='GPLv2',
    keywords = "fs dropbox",
    include_package_data=True,
    entry_points = {
        'console_scripts': ['cuckoodrive=cuckoodrive:main']
    }
)
