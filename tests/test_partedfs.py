# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from mock import Mock, call

from pytest import fixture, raises, mark
from fs.memoryfs import MemoryFS
from os import urandom
from drive.partedfs import FilePart, PartedFile, InvalidFilePointerLocation, PartedFS


def kb(value):
    """
    Helper method to return value in KB as value in Bytes
    :param value in Kilobytes
    :return: value in Bytes
    """
    return value * 1024


class TestPartedFS:
    @fixture
    def fs(self):
        wrapped_fs = MemoryFS()
        wrapped_fs.setcontents("backup.tar.part0", data=urandom(kb(4)))
        wrapped_fs.setcontents("backup.tar.part1", data=urandom(kb(4)))
        wrapped_fs.setcontents("backup.tar.part2", data=urandom(kb(2)))
        return PartedFS(wrapped_fs, kb(4))

    def test_exists_returns_true_when_first_part_could_be_found(self, fs):
        #Act & Assert
        assert fs.exists("backup.tar")

    def test_open_for_reading_returns_parted_file_with_all_parts(self, fs):
        #Act
        parted_file = fs.open("backup.tar", mode="r")
        #Assert
        assert len(parted_file._parts) == 3

    def test_remove_deletes_all_parts(self, fs):
        #Arrange
        fs.wrapped_fs.remove = Mock()
        #Act
        fs.remove("backup.tar")
        #Assert
        fs.wrapped_fs.remove.assert_has_calls([
            call("/backup.tar.part0"),
            call("/backup.tar.part1"),
            call("/backup.tar.part2")], any_order=True)


class TestFilePart:
    @fixture
    def file_part(self):
        fs = MemoryFS()
        mode = "wb+"
        wrapped_file = fs.open("backup.tar", mode)
        return FilePart(wrapped_file=wrapped_file, mode=mode,
                        max_size=kb(4), path="backup.tar", fs=fs)

    def test_fill_with_less_data_returns_none(self, file_part):
        #Act
        data = file_part.fill(data=urandom(kb(3)))
        #Assert
        assert data is None

    def test_fill_with_too_much_data_returns_unwritten_data(self, file_part):
        #Act
        data = file_part.fill(data=urandom(kb(5)))
        #Assert
        assert len(data) == kb(1)


class TestPartedFile:
    @fixture
    def parted_file(self):
        return PartedFile(path="cuckoo.tar", mode="wb+", fs=MemoryFS(), max_part_size=kb(4))

    @fixture
    def file_parts(self, parted_file):
        parts = []
        fs = MemoryFS()
        for i in range(3):
            path = "cuckoo.tar.part" + str(i)
            mode = "wb+"
            f = fs.open(path, mode)
            cf = FilePart(f, mode, parted_file.max_part_size, path, fs)
            if i == 3:
                cf.write(urandom(kb(2)))
            else:
                cf.write(urandom(parted_file.max_part_size))
            parts.append(cf)

        return parts

    def test_current_part_returns_none_if_no_parts_exist(self, parted_file):
        #Act & Assert
        assert parted_file.current_part is None

    def test_current_part_returns_last_part_when_file_pointer_is_on_last_byte(self, parted_file, file_parts):
        #Arrange
        parted_file._parts = file_parts
        parted_file._fpointer = 2 * kb(4) + kb(2)

        #Act & Assert
        assert parted_file.current_part == file_parts[2]

    def test_current_part_returns_first_part_when_file_pointer_is_there(self, parted_file, file_parts):
        #Arrange
        parted_file._parts = file_parts
        parted_file._fpointer = 1 * kb(3)
        #Act & Assert
        assert parted_file.current_part == file_parts[0]

    def test_current_part_returns_first_part_when_file_pointer_is_max_part_size(self, parted_file, file_parts):
        #Arrange
        parted_file._parts = file_parts
        parted_file._fpointer = 1 * kb(4)
        #Act & Assert
        assert parted_file.current_part == file_parts[0]

    def test_current_part_raises_error_when_file_pointer_is_bigger_than_parts(self, parted_file, file_parts):
        #Arrange
        parted_file._parts = file_parts
        parted_file._fpointer = 4 * kb(4)
        #Act & Assert
        with raises(InvalidFilePointerLocation):
            _ = parted_file.current_part

    def test_write_set_file_pointer_to_last_position(self, parted_file):
        #Act
        parted_file._write(urandom(kb(1)))
        #Assert
        assert parted_file._fpointer == kb(1)

    def test_write_small_amount_is_written_to_first_part(self, parted_file):
        #Act
        parted_file._write(urandom(kb(1)), flushing=True)
        parted_file._seek(offset=0, whence=1)
        #Assert
        assert kb(1) == len(parted_file._parts[0].read())

    def test_write_big_amount_expands_to_parts(self, parted_file):
        #Act
        parted_file._write(urandom(kb(12)), flushing=True)
        parted_file._seek(offset=0, whence=1)
        #Assert
        assert len(parted_file._parts) == 3

    def test_read_returns_none_after_all_has_been_read(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(3)), flushing=True)
        parted_file._seek(offset=0, whence=0)
        #Act
        parted_file._read()
        eof = parted_file._read()
        #Assert
        assert eof is None

    def test_read_returns_what_was_written(self, parted_file):
        #Arrange
        data = urandom(kb(5))
        parted_file._write(data, flushing=True)
        parted_file._seek(offset=0, whence=1)
        #Act
        read_data = parted_file._read()
        #Act & Assert
        assert len(data) == len(read_data)

    def test_read_raises_error_when_sizehint_is_bigger_than_max_part_size(self, parted_file):
        #Act & Assert
        with raises(NotImplementedError):
            parted_file._read(sizehint=kb(5))

    def test_read_returns_data_with_given_sizehint(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(5)), flushing=True)
        parted_file._seek(offset=0, whence=0)
        #Act
        data = parted_file._read(sizehint=kb(1))
        #Assert
        assert len(data) == kb(1)

    def test_read_in_chunks_returns_all_written_data(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(8)), flushing=True)
        parted_file._seek(offset=0, whence=0)
        #Act
        chunk1 = parted_file._read(sizehint=kb(3))
        chunk2 = parted_file._read(sizehint=kb(3))
        chunk3 = parted_file._read(sizehint=kb(3))
        #Assert
        assert len(chunk1) == kb(3)
        assert len(chunk2) == kb(3)
        assert len(chunk3) == kb(2)

    def test_read_returns_none_when_eof_reached(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(4)), flushing=True)
        parted_file._seek(offset=0, whence=0)
        #Act
        parted_file._read(sizehint=kb(2))
        parted_file._read(sizehint=kb(2))
        eof = parted_file._read(sizehint=kb(2))
        #Assert
        assert eof is None

    def test_seek_can_go_to_start_of_file(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(1)))
        #Act
        parted_file._seek(offset=0, whence=0)
        #Assert
        assert parted_file._fpointer == 0 and parted_file.current_part == parted_file._parts[0]

    def test_seek_can_go_to_correct_part(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(6)))
        #Act
        parted_file._seek(offset=kb(5), whence=0)
        #Assert
        assert parted_file._fpointer == kb(5) and parted_file.current_part == parted_file._parts[1]

    def test_tell_returns_file_pointer(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(5)))
        #Act
        parted_file._seek(offset=kb(2), whence=0)
        pos = parted_file._tell()
        #Assert
        assert pos == kb(2)