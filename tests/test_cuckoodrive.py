from __future__ import print_function, division, absolute_import, unicode_literals

from pytest import fixture
from fs.memoryfs import MemoryFS
from fs.wrapfs.limitsizefs import LimitSizeFS

from drive.cuckoodrive import StorageProvider, StorageAllocation, StorageAllocator


def mb(value):
    """
    Helper method to return value in MB as value in Bytes
    :param value in Megabytes
    :return: value in Bytes
    """
    return value * 1024 * 1024


class TestStorageAllocator:
    @fixture
    def allocator(self):
        self.dropbox = StorageProvider(name="dropbox", fs=LimitSizeFS(MemoryFS(), mb(230)))
        self.googledrive = StorageProvider(name="googledrive", fs=LimitSizeFS(MemoryFS(), mb(120)))
        return StorageAllocator(providers=[self.dropbox, self.googledrive])

    def test_write_small_file_returns_location_with_most_free_space(self, allocator):
        #Arrange
        filesize = mb(30)
        #Act
        allocations = allocator.allocate(filesize)
        #Assert
        assert StorageAllocation((mb(0), mb(30)), self.dropbox) == allocations[0]
    
    def test_write_big_file_returns_multiple_allocations(self, allocator):
        #Arrange
        filesize = mb(330)
        #Act
        allocations = allocator.allocate(filesize)
        #Assert
        assert allocations == [StorageAllocation((mb(0), mb(100)), self.dropbox),
                               StorageAllocation((mb(100), mb(200)), self.dropbox),
                               StorageAllocation((mb(200), mb(300)), self.googledrive),
                               StorageAllocation((mb(300), mb(330)), self.googledrive)]