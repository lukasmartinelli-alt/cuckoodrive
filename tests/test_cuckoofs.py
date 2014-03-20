# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from _pytest.python import fixture, raises

from fs.memoryfs import MemoryFS, MemoryFile
from fs.wrapfs.limitsizefs import LimitSizeFS

from drive.cuckoofs import CuckooFile, FileAllocator, AllocationSizeError
from fs.wrapfs.readonlyfs import

def mb(value):
    """
    Helper method to return value in MB as value in Bytes
    :param value in Megabytes
    :return: value in Bytes
    """
    return value * 1024 * 1024


# noinspection PyMethodMayBeStatic
class TestFileAllocator:
    @fixture
    def allocator(self):
        dropbox = LimitSizeFS(MemoryFS(), mb(220))
        googledrive = LimitSizeFS(MemoryFS(), mb(110))
        return FileAllocator(filesystems=[dropbox, googledrive], allocation_size=mb(10))
    def test_allocate_file_returns_new_file(self, allocator):
        #Act
        f = allocator.allocate_file("bigfile.tar.gz")
        #Assert
        assert isinstance(f.__class__, MemoryFile.__class__)

    def test_allocate_file_raises_error_when_size_too_big(self, allocator):
        #Arrange
        allocator.allocation_size = mb(300)
        #Act & Assert
        with raises(AllocationSizeError):
            allocator.allocate_file("bigfile.tar.gz")

    def test_best_fs_returns_fs_with_most_space(self, allocator):
        #Act
        best_fs = allocator.best_fs()
        #Assert
        assert best_fs == allocator.filesystems[0]

    def test_free_space_returns_space_left_inclusive_allcoations(self, allocator):
        #Arrange
        dropbox = allocator.filesystems[0]
        googledrive = allocator.filesystems[1]
        allocator.allocations[dropbox] = mb(100)
        #Act
        dropbox_free_space = allocator.free_space(dropbox)
        googledrive_free_space = allocator.free_space(googledrive)
        #Assert
        assert dropbox_free_space == mb(120)
        assert googledrive_free_space == mb(110)


# noinspection PyMethodMayBeStatic
class TestCuckooFile:
    @fixture
    def allocator(self):
        dropbox = LimitSizeFS(MemoryFS(), mb(220))
        googledrive = LimitSizeFS(MemoryFS(), mb(110))
        return FileAllocator(filesystems=[dropbox, googledrive], allocation_size=mb(10))

    @fixture
    def test_file(self, allocator):
        return CuckooFile(path="bigfile.tar.gz", file_allocator=allocator)

    def test_write(self, test_file):
        test_file.write("salalalalalalala")
        test_file.close()

    def test_read(self):
        pass

    def test_seek(self):
        pass

    def test_tell(self):
        pass

    def test_truncate(self):
        pass