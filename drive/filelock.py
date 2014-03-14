# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.errors import FSError

import time


class FileLockException(Exception):
    pass


class FileLock(object):
    """ A file locking mechanism that has context-manager support so
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.

        All credit for this code goes to Evan Fosmark who implemented the
        original version. I simply adapted it so that it can be used
        with the pyfilesystem module.

        Original Repository: https://github.com/dmfrey/FileLock
    """

    def __init__(self, fs, file_name=".lock", timeout=10, delay=.05):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.fs = fs
        self.is_locked = False
        self.file_name = file_name
        self.timeout = timeout
        self.delay = delay

    def acquire(self):
        """ Acquire the lock, if possible. If the lock is in use, it check again
            every `wait` seconds. It does this until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it throws
            an exception.
        """
        start_time = time.time()
        while True:
            try:
                if not self.fs.exists(self.file_name):
                    self.lockfile = self.fs.open(self.file_name, 'w')
                    break
                else:
                    if (time.time() - start_time) >= self.timeout:
                        raise FileLockException("Timeout occured.")
                    time.sleep(self.delay)
            except FSError:
                raise
        self.is_locked = True

    def release(self):
        """ Get rid of the lock by deleting the lockfile.
            When working in a `with` statement, this gets automatically
            called at the end.
        """
        if self.is_locked:
            self.lockfile.close()
            self.fs.remove(self.file_name)
            self.is_locked = False

    def __enter__(self):
        """ Activated when used in the with statement.
            Should automatically acquire a lock to be used in the with block.
        """
        if not self.is_locked:
            self.acquire()
        return self

    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        if self.is_locked:
            self.release()

    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        self.release()
