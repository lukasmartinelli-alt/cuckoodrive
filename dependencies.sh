# Install fs (pyfilesystem)
svn checkout http://pyfilesystem.googlecode.com/svn/trunk/ pyfilesystem
cd pyfilesystem
python setup.py install
cd ..
rm -r pyfilesystem

# Install amazon-cloud-drive
svn checkout http://pyamazonclouddrive.googlecode.com/svn/trunk/ amazon-cloud-drive
cd amazon-cloud-drive
python setup.py install
cd ..
rm -r amazon-cloud-drive
