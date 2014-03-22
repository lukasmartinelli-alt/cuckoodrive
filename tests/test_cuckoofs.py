# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from pytest import fixture, raises

from fs.memoryfs import MemoryFS
from os import urandom

from drive.cuckoofs import CuckooRemoteFS, CuckooFile, CuckooFilePart, CuckooFilePartMissingError


def kb(value):
    """
    Helper method to return value in KB as value in Bytes
    :param value in Kilobytes
    :return: value in Bytes
    """
    return value * 1024


class TestCuckooRemoteFS:
    @fixture
    def remote_fs(self):
        return CuckooRemoteFS(MemoryFS(), kb(100))

    def test_free_space_returns_difference_between_max_size_and_cur_size(self, remote_fs):
        #Arrange
        remote_fs.cur_size = kb(30)
        #Act
        free_space = remote_fs.free_space()
        #Assert
        assert free_space == kb(70)


class TestCuckooFile:
    @fixture
    def remote_filesystems(self):
        return [
            CuckooRemoteFS(MemoryFS(), kb(120)),
            CuckooRemoteFS(MemoryFS(), kb(220))]

    @fixture
    def cuckoo_file(self, remote_filesystems):
        return CuckooFile(path="cuckoo.tar", mode="wb+", max_part_size=kb(4),
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
                cf.write(urandom(kb(2)))
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
        cuckoo_file._expand_part()
        #Act
        data = cuckoo_file._fill(data=urandom(kb(3)), part=cuckoo_file._parts[0])
        #Assert
        assert data is None

    def test_fill_with_too_much_data_returns_unwritten_data(self, cuckoo_file):
        #Arrange
        cuckoo_file._expand_part()
        #Act
        data = cuckoo_file._fill(data=urandom(kb(5)), part=cuckoo_file._parts[0])
        #Assert
        assert len(data) == kb(1)

    def test_current_part_returns_none_if_no_parts_exist(self, cuckoo_file):
        #Act & Assert
        assert cuckoo_file.current_part is None

    def test_current_part_returns_last_part_when_file_pointer_is_on_last_byte(self, cuckoo_file, cuckoo_file_parts):
        #Arrange
        cuckoo_file._parts = cuckoo_file_parts
        cuckoo_file._fpointer = 2 * kb(4) + kb(2)

         #Act & Assert
        assert cuckoo_file.current_part == cuckoo_file_parts[2]

    def test_current_part_returns_first_part_when_file_pointer_is_there(self, cuckoo_file, cuckoo_file_parts):
        #Arrange
        cuckoo_file._parts = cuckoo_file_parts
        cuckoo_file._fpointer = 1 * kb(3)
        #Act & Assert
        assert cuckoo_file.current_part == cuckoo_file_parts[0]

    def test_current_part_returns_first_part_when_file_pointer_is_max_part_size(self, cuckoo_file, cuckoo_file_parts):
        #Arrange
        cuckoo_file._parts = cuckoo_file_parts
        cuckoo_file._fpointer = 1 * kb(4)
        #Act & Assert
        assert cuckoo_file.current_part == cuckoo_file_parts[0]

    def test_current_part_raises_error_when_file_pointer_is_bigger_than_parts(self, cuckoo_file, cuckoo_file_parts):
        #Arrange
        cuckoo_file._parts = cuckoo_file_parts
        cuckoo_file._fpointer = 4 * kb(4)
        #Act & Assert
        with raises(CuckooFilePartMissingError):
            _ = cuckoo_file.current_part

    def test_write_set_file_pointer_to_last_position(self, cuckoo_file):
        #Act
        cuckoo_file._write(urandom(kb(1)))
        #Assert
        assert cuckoo_file._fpointer == kb(1)

    def test_write_small_amount_is_written_to_first_part(self, cuckoo_file):
        #Act
        cuckoo_file._write(urandom(kb(1)), flushing=True)
        cuckoo_file._seek(offset=0, whence=1)
        #Assert
        assert kb(1) == len(cuckoo_file._parts[0].read())

    def test_write_big_amount_expands_to_parts(self, cuckoo_file):
        #Act
        cuckoo_file._write(urandom(kb(12)), flushing=True)
        cuckoo_file._seek(offset=0, whence=1)
        #Assert
        assert len(cuckoo_file._parts) == 3

    def test_read_returns_what_was_written(self, cuckoo_file):
        #Arrange
        data = urandom(kb(5))
        cuckoo_file._write(data, flushing=True)
        cuckoo_file._seek(offset=0, whence=1)
        #Act & Assert
        assert len(data) == len(cuckoo_file._read())

    def test_read_raises_error_when_sizehint_is_bigger_than_max_part_size(self, cuckoo_file):
        #Act & Assert
        with raises(NotImplementedError):
            cuckoo_file._read(sizehint=kb(5))

    def test_read_returns_data_with_given_sizehint(self, cuckoo_file):
        #Arrange
        cuckoo_file._write(urandom(kb(5)), flushing=True)
        cuckoo_file._seek(offset=0, whence=0)
        #Act
        data = cuckoo_file._read(sizehint=kb(1))
        #Assert
        assert len(data) == kb(1)

    def test_read_in_chunks_returns_all_written_data(self, cuckoo_file):
        #Arrange
        cuckoo_file._write(urandom(kb(8)), flushing=True)
        cuckoo_file._seek(offset=0, whence=0)
        #Act
        chunk1 = cuckoo_file._read(sizehint=kb(3))
        chunk2 = cuckoo_file._read(sizehint=kb(3))
        chunk3 = cuckoo_file._read(sizehint=kb(3))
        #Assert
        assert len(chunk1) == kb(3)
        assert len(chunk2) == kb(3)
        assert len(chunk3) == kb(2)

    def test_read_returns_none_when_eof_reached(self, cuckoo_file):
        #Arrange
        cuckoo_file._write(urandom(kb(4)), flushing=True)
        cuckoo_file._seek(offset=0, whence=0)
        #Act
        cuckoo_file._read(sizehint=kb(2))
        cuckoo_file._read(sizehint=kb(2))
        eof = cuckoo_file._read(sizehint=kb(2))
        #Assert
        assert eof is None

