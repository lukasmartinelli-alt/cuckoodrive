# Install fs (pyfilesystem)
echo "Checking out pyfilesystem to install it"
svn checkout http://pyfilesystem.googlecode.com/svn/trunk/ pyfilesystem
cd pyfilesystem
echo "Installing pyfilesystem..."
python setup.py install
echo "Installed pyfilesystem"
cd ..
rm -r pyfilesystem
echo "Cleaned up pyfilesystem"


# Install amazon-cloud-drive
echo "Checking out amazon-cloud-drive to install it"
svn checkout http://pyamazonclouddrive.googlecode.com/svn/trunk/ amazon-cloud-drive
echo "Installing amazon-cloud-drive..."
cd amazon-cloud-drive
echo "Installed amazon-cloud-drive"
python setup.py install
cd ..
rm -r amazon-cloud-drive
echo "Cleaned up amazon-cloud-drive"
