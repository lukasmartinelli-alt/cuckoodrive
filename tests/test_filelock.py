# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from pytest import fixture, raises

from fs.memoryfs import MemoryFS

from cuckoodrive.filelock import FileLock, FileLockError


class TestFileLock:
    """Test implementation of the FileLock"""

    @fixture
    def fs(self, request):
        """Create a MemoryFS for testing. The finalizer removes all files in it"""
        fs = MemoryFS()

        def cleanup():
            for file_path in fs.listdir(files_only=True):
                fs.remove(file_path)

        request.addfinalizer(cleanup)
        return fs

    def test_acquire_lock_and_close_it(self, fs):
        # Act
        with FileLock(fs):
            assert True  # We got lock successfully

    def test_acquire_when_file_already_exists(self, fs):
        # Arrange
        with fs.open(".lock", "w"):
            # Act & Assert
            with raises(FileLockError):
                with FileLock(fs, timeout=1):
                    assert False  # We shouldnt get the lock
