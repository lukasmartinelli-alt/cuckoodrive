# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os import urandom
from fs.memoryfs import MemoryFS
from pytest import fixture
from drive.partedfs import PartedFS
from drive.utils import kb


class FSTestBase(object):
    """
    A generic test suite that is used to test all implementations of the file system interface.
    This should mimic real use cases and test the filesystem intensely, so we can be sure everything works.

    This will expect certain behaviours that are defined in the pyFilesystem interface.
    """
    @fixture
    def fs(self, request):
        raise NotImplementedError("Please provide an instance of your filesystem here.")

    def test_create_new_file_should_exist_afterwards(self, fs):
        #Act
        with fs.open("my_wonderful_new_file.txt", mode="wb") as f:
            f.write(urandom(kb(4)))
        #Assert
        assert fs.exists("my_wonderful_new_file.txt")
        assert fs.getsize("my_wonderful_new_file.txt") == kb(4)

    def test_what_was_written_should_be_read(self, fs):
        #Arrange
        written_data = urandom(kb(4))
        #Act
        with fs.open("my_wonderful_new_file.txt", mode="wb") as f:
            f.write(written_data)
        with fs.open("my_wonderful_new_file.txt", mode="rb") as f:
            read_data = f.read()
        #Assert
        assert len(written_data) == len(read_data)

class TestPartedFS(FSTestBase):
    @fixture
    def fs(self, request):
        return PartedFS(MemoryFS(), max_part_size=kb(4))