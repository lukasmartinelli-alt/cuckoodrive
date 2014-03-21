# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from _pytest.python import fixture, raises

from fs.memoryfs import MemoryFS
from os import urandom

from drive.cuckoofs import CuckooRemoteFS, CuckooFile, CuckooFilePart, CuckooFilePartMissingError


def mb(value):
    """
    Helper method to return value in MB as value in Bytes
    :param value in Megabytes
    :return: value in Bytes
    """
    return value * 1024 * 1024


class TestCuckooRemoteFS:
    @fixture
    def remote_fs(self):
        return CuckooRemoteFS(MemoryFS(), mb(100))

    def test_free_space_returns_difference_between_max_size_and_cur_size(self, remote_fs):
        #Arrange
        remote_fs.cur_size = mb(30)
        #Act
        free_space = remote_fs.free_space()
        #Assert
        assert free_space == mb(70)


class TestCuckooFile:
    @fixture
    def remote_filesystems(self):
        return [
            CuckooRemoteFS(MemoryFS(), mb(120)),
            CuckooRemoteFS(MemoryFS(), mb(220))]

    @fixture
    def cuckoo_file(self, remote_filesystems):
        return CuckooFile(path="cuckoo.tar", mode="wb+", max_part_size=mb(4),
                          remote_filesystems=remote_filesystems)

    @fixture
    def cuckoo_file_parts(self, cuckoo_file):
        parts = []
        fs = cuckoo_file.remote_filesystems[0]
        for i in range(3):
            path = "cuckoo.tar.part" + str(i)
            mode = "wb+"
            f = fs.open(path, mode)
            cf = CuckooFilePart(f, mode, cuckoo_file.max_part_size, fs, path)
            if i == 3:
                cf.write(urandom(mb(2)))
            else:
                cf.write(urandom(cuckoo_file.max_part_size))
            parts.append(cf)

        return parts

    def test_best_fs_returns_fs_with_most_space(self, cuckoo_file):
        #Act
        best_fs = cuckoo_file.best_fs
        #Assert
        assert best_fs == cuckoo_file.remote_filesystems[1]

    def test_fill_with_less_data_returns_none(self, cuckoo_file):
        #Arrange
        cuckoo_file._expand()
        #Act
        data = cuckoo_file._fill(data=urandom(mb(3)), part=cuckoo_file._parts[0])
        #Assert
        assert data is None

    def test_fill_with_too_much_data_returns_unwritten_data(self, cuckoo_file):
        #Arrange
        cuckoo_file._expand()
        #Act
        data = cuckoo_file._fill(data=urandom(mb(5)), part=cuckoo_file._parts[0])
        #Assert
        assert len(data) == mb(1)

    def test_current_part_returns_none_if_no_parts_exist(self, cuckoo_file):
        #Act & Assert
        assert cuckoo_file.current_part is None

    def test_current_part_returns_last_part_when_file_pointer_is_on_last_byte(self, cuckoo_file, cuckoo_file_parts):
        #Arrange
        cuckoo_file._parts = cuckoo_file_parts
        cuckoo_file._fpointer = 2 * mb(4) + mb(2)

         #Act & Assert
        assert cuckoo_file.current_part == cuckoo_file_parts[2]

    def test_current_part_returns_first_part_when_file_pointer_is_there(self, cuckoo_file, cuckoo_file_parts):
        #Arrange
        cuckoo_file._parts = cuckoo_file_parts
        cuckoo_file._fpointer = 1 * mb(3)
        #Act & Assert
        assert cuckoo_file.current_part == cuckoo_file_parts[0]

    def test_current_part_returns_first_part_when_file_pointer_is_max_part_size(self, cuckoo_file, cuckoo_file_parts):
        #Arrange
        cuckoo_file._parts = cuckoo_file_parts
        cuckoo_file._fpointer = 1 * mb(4)
        #Act & Assert
        assert cuckoo_file.current_part == cuckoo_file_parts[0]

    def test_current_part_raises_error_when_file_pointer_is_bigger_than_parts(self, cuckoo_file, cuckoo_file_parts):
        #Arrange
        cuckoo_file._parts = cuckoo_file_parts
        cuckoo_file._fpointer = 4 * mb(4)
        #Act & Assert
        with raises(CuckooFilePartMissingError):
            _ = cuckoo_file.current_part

    def test_write_set_file_pointer_to_last_position(self, cuckoo_file):
        #Act
        cuckoo_file._write(urandom(mb(1)))
        #Assert
        assert cuckoo_file._fpointer == mb(1)

    def test_write_small_amount_is_written_to_first_part(self, cuckoo_file):
        #Act
        cuckoo_file._write(urandom(mb(1)), flushing=True)
        cuckoo_file._seek(offset=0, whence=1)
        #Assert
        assert mb(1) == len(cuckoo_file._parts[0].read())

    def test_write_big_amount_expands_to_parts(self, cuckoo_file):
        #Act
        cuckoo_file._write(urandom(mb(12)), flushing=True)
        cuckoo_file._seek(offset=0, whence=1)
        #Assert
        assert len(cuckoo_file._parts) == 3
