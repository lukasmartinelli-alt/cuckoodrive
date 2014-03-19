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

# Install amazon-cloud-drive
echo "Checking out amazon-cloud-drive with svn to install it"
svn checkout http://pyamazonclouddrive.googlecode.com/svn/trunk/ amazon-cloud-drive
echo "Installing amazon-cloud-drive..."
cd amazon-cloud-drive
echo "Installed amazon-cloud-drive"
python setup.py install
cd ..

cd ..
