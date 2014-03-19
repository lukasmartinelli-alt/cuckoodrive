from __future__ import print_function, division, absolute_import, unicode_literals

from pytest import fixture
from fs.memoryfs import MemoryFS
from fs.wrapfs.limitsizefs import LimitSizeFS

from drive.storage import Storage, StorageAllocation, StorageAllocator


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
        dropbox = Storage(name="dropbox", fs=LimitSizeFS(MemoryFS(), mb(220)), max_filesize=mb(100))
        googledrive = Storage(name="googledrive", fs=LimitSizeFS(MemoryFS(), mb(110)), max_filesize=mb(100))
        return StorageAllocator(storages=[dropbox, googledrive])

    def test_write_small_file_returns_location_with_most_free_space(self, allocator):
        #Arrange
        filesize = mb(30)
        dropbox = allocator.storages[0]
        #Act
        allocations = allocator.allocate(filesize)
        #Assert
        assert StorageAllocation((mb(0), mb(30)), dropbox) == allocations[0]

    def test_write_big_file_returns_multiple_allocations(self, allocator):
        #Arrange
        filesize = mb(330)
        dropbox = allocator.storages[0]
        googledrive = allocator.storages[1]
        #Act
        allocations = allocator.allocate(filesize)
        #Assert
        expected_allocations = [StorageAllocation((mb(0), mb(100)), dropbox),
                                StorageAllocation((mb(100), mb(200)), dropbox),
                                StorageAllocation((mb(200), mb(300)), googledrive),
                                StorageAllocation((mb(300), mb(320)), dropbox),
                                StorageAllocation((mb(320), mb(330)), googledrive)]
        assert expected_allocations == allocations