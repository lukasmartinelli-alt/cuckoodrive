#!/bin/sh
mkdir .tmp
cd .tmp

# Install fs (pyfilesystem)
echo "Checking out pyfilesystem with svn to install it"
svn checkout http://pyfilesystem.googlecode.com/svn/trunk/ pyfilesystem
cd pyfilesystem
echo "Installing pyfilesystem..."
python setup.py install
echo "Installed pyfilesystem"
cd ..