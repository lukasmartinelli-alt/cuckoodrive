from __future__ import print_function, division, absolute_import, unicode_literals
from os import urandom

from pytest import fixture

from fs.memoryfs import MemoryFS

from drive.cuckoodrive import CuckooDriveFS


class TestCuckooDriveFS:
    """Test implementation of the CuckooDriveFS"""
    @fixture
    def providers():
        dropbox = MemoryFS()
        googledrive = MemoryFS()
        onedrive = MemoryFS()
        mega = MemoryFS()
        return [dropbox, googledrive, onedrive, mega]

    @fixture
    def fs():
        return CuckooDriveFS()

    def open_write_large_file_should_split_into_chunks(self, fs):
        chunk_size = 4194304
        buffer_size = 1024
        #Arrange
        path = "backup.zip"
        #Act
        with fs.open(path, "w") as file:
            for _ in range(0, chunk_size / buffer_size):
                file.write(urandom(buffer_size))
        #Assert
        assert ["backup.zip.part1", "backup.zip.part2"] == fs.listdir()
