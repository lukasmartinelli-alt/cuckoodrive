from setuptools import setup


with open('README.rst') as fh:
    long_description = fh.read()


setup(
    name="cuckoodrive",
    version="0.0.1",
    author="Lukas Martinelli",
    author_email="me@lukasmartinelli.ch",
    description=("Aggregates all the free space provided on various \
                 cloud storage providers into one big drive."),
    license='GPLv2',
    keywords = "fs dropbox",
    url = "https://github.com/lukasmartinelli/cuckoodrive",
    packages=['cuckoodrive'],
    install_requires=['fs', 'dropbox', 'docopt'],
    include_package_data=True,
    long_description=long_description,
    scripts=['cuckoodrive/cuckoo']
)
