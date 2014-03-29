# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os import urandom
from datetime import timedelta, date

from mock import Mock, call
from pytest import fixture, raises, mark

from fs.memoryfs import MemoryFS
from fs.errors import ResourceNotFoundError, ResourceInvalidError

from drive.partedfs import PartedFS, PartedFile, FilePart, InvalidFilePointerLocation
from drive.utils import kb


class TestPartedFS(object):
    @fixture
    def fs(self):
        return PartedFS(MemoryFS(), kb(4))

    @fixture
    def fs_with_folder_structure(self, fs):
        fs.wrapped_fs.setcontents("backup.tar.part0", data=urandom(kb(4)))
        fs.wrapped_fs.setcontents("backup.tar.part1", data=urandom(kb(4)))
        fs.wrapped_fs.setcontents("README.txt.part0", data=urandom(kb(1)))
        fs.wrapped_fs.makedir("older_backups")
        return fs

    @fixture
    def fs_with_test_file(self, fs):
        fs.wrapped_fs.setcontents("backup.tar.part0", data=urandom(kb(4)))
        fs.wrapped_fs.setcontents("backup.tar.part1", data=urandom(kb(4)))
        return fs

    def test_encode_should_return_file_with_part0_extension(self, fs):
        #Arrange
        path = "backup.tar"
        #Act
        encoded_path = fs._encode(path)
        #Assert
        assert encoded_path == "backup.tar.part0"

    def test_encode_appends_given_index_to_extension(self, fs):
        #Arrange
        path = "backup.tar"
        #Act
        encoded_path = fs._encode(path, part_index=2)
        #Assert
        assert encoded_path == "backup.tar.part2"

    def test_decode_should_return_part_without_part_extension(self, fs):
        #Arrange
        encoded_path = "backup.tar.part1"
        #Act
        decoded_path = fs._decode(encoded_path)
        #Assert
        assert decoded_path == "backup.tar"

    def test_listparts_returns_all_parts_for_a_path(self, fs_with_test_file):
        #Act
        listing = fs_with_test_file.listparts("backup.tar")
        #Assert
        assert listing == ["backup.tar.part0", "backup.tar.part1"]

    def test_exists_returns_true_when_first_part_could_be_found(self, fs):
        #Arrange
        fs.wrapped_fs.setcontents("backup.tar.part0", data=urandom(kb(4)))
        #Act & Assert
        assert fs.exists("backup.tar")

    def test_isfile_returns_wether_the_first_part_is_file(self, fs):
        #Arrange
        fs.wrapped_fs.isfile = Mock()
        #Act
        fs.isfile("backup.tar")
        #Act
        fs.wrapped_fs.isfile.assert_called_once_with("backup.tar.part0")

    def test_exists_returns_false_when_first_part_is_not_found(self, fs):
        #Act & Assert
        assert not fs.exists("backup.tar")

    def test_remove_deletes_all_parts(self, fs):
        #Arrange
        fs.wrapped_fs.setcontents("backup.tar.part0", data=urandom(kb(4)))
        fs.wrapped_fs.setcontents("backup.tar.part1", data=urandom(kb(4)))
        fs.wrapped_fs.setcontents("backup.tar.part2", data=urandom(kb(2)))
        fs.wrapped_fs.remove = Mock()
        #Act
        fs.remove("backup.tar")
        #Assert
        fs.wrapped_fs.remove.assert_has_calls([
                                                  call("backup.tar.part0"),
                                                  call("backup.tar.part1"),
                                                  call("backup.tar.part2")], any_order=True)

    def test_listdir_returns_only_directories(self, fs_with_folder_structure):
        #Act
        listing = fs_with_folder_structure.listdir(dirs_only=True)
        #Assert
        assert listing == ["older_backups"]

    def test_listdir_returns_only_files(self, fs_with_folder_structure):
        #Act
        listing = fs_with_folder_structure.listdir(files_only=True)
        #Assert
        assert listing == ["README.txt", "backup.tar"]

    def test_listdir_returns_files_and_directories(self, fs_with_folder_structure):
        #Act
        listing = fs_with_folder_structure.listdir()
        #Assert
        assert listing == ["older_backups", "README.txt", "backup.tar"]

    def test_listdirinfo_raises_error_when_not_exists(self, fs):
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.listdirinfo("random_dir")

    def test_listdirinfo_returns_path_and_infodict(self, fs_with_folder_structure):
        #Arrange
        info = {}
        fs_with_folder_structure.getinfo = Mock(return_value=info)
        #Act
        listing = fs_with_folder_structure.listdirinfo()
        #Assert
        assert listing == [("older_backups", info), ("README.txt", info), ("backup.tar", info)]


    def test_open_if_w_in_mode_all_parts_should_be_removed(self, fs_with_test_file):
        #Arrange
        fs_with_test_file.remove = Mock()
        #Act
        fs_with_test_file.open("backup.tar", mode="w")
        #Assert
        fs_with_test_file.remove.assert_called_once_with("backup.tar")

    def test_open_raises_error_if_w_and_a_not_in_mode(self, fs):
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.open("i_dont_exist", mode="r")

    def test_open_raises_error_if_path_is_directory(self, fs):
        #Arrange
        fs.makedir("backups")
        #Act & Assert
        with raises(ResourceInvalidError):
            fs.open("backups", mode="w")

    def test_open_raises_error_if_path_does_not_exist(self, fs):
        #Arrange
        path = "backup.tar"
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.open(path, mode="r")
        with raises(ResourceNotFoundError):
            fs.open(path, mode="r+")

    def test_open_creates_empty_file_if_path_does_not_exist(self, fs):
        #Arrange
        path = "backup.tar"
        #Act
        f = fs.open(path, mode="w")
        #Assert
        assert len(f.parts) == 1

    def test_open_uses_existing_parts_if_path_exists(self, fs_with_test_file):
        #Act
        f = fs_with_test_file.open("backup.tar", mode="r+")
        #Assert
        assert len(f.parts) == 2

    def test_open_with_existing_parts_opens_them_in_correct_order(self, fs):
        #Arrange
        fs.wrapped_fs.setcontents("backup.tar.part0", data=urandom(kb(4)))
        fs.wrapped_fs.setcontents("backup.tar.part1", data=urandom(kb(4)))
        fs.wrapped_fs.setcontents("backup.tar.part2", data=urandom(kb(2)))
        #Act
        f = fs.open("backup.tar", mode="r+")
        #Assert
        created_parts = [part.name for part in f.parts]
        assert created_parts == ["backup.tar.part0", "backup.tar.part1", "backup.tar.part2"]

    def test_rename_raises_error_if_not_exists(self, fs):
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.rename("you_cant_name_me", "you_cant_name_me2")

    def test_rename_renames_all_parts(self, fs_with_test_file):
        #Arrange
        fs_with_test_file.wrapped_fs.rename = Mock()
        #Act
        fs_with_test_file.rename("backup.tar", "backup2.tar")
        #Assert
        fs_with_test_file.wrapped_fs.rename.assert_has_calls([
                                                                 call("backup.tar.part0", "backup2.tar.part0"),
                                                                 call("backup.tar.part1", "backup2.tar.part1")],
                                                             any_order=True)

    def test_getsize_returns_sum_of_parts(self, fs_with_test_file):
        #Act
        size = fs_with_test_file.getsize("backup.tar")
        #assert
        assert size == kb(8)

    def test_getsize_raises_error_if_not_exists(self, fs):
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.getsize("im_invisible")

    def test_getinfo_raises_error_if_not_exists(self, fs):
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.getinfo("im_invisible")

    def test_isdir_calls_underyling_fs(self, fs):
        #Arrange
        path = "/"
        fs.wrapped_fs.isdir = Mock()
        #Act
        fs.isdir(path)
        #Arrange
        fs.wrapped_fs.isdir.assert_called_once_with(path)

    def test_makedir_calls_underyling_fs(self, fs):
        #Arrange
        path = "folder"
        fs.wrapped_fs.makedir = Mock()
        #Act
        fs.makedir(path)
        #Arrange
        fs.wrapped_fs.makedir.assert_called_once_with(path)

    def test_getinfo_for_root_returns_information(self, fs):
        #Act
        info = fs.getinfo("/")
        #Assert
        assert "created_time" in info
        assert "modified_time" in info
        assert "accessed_time" in info

    def test_getinfo_returns_directory_info_for_dir(self, fs):
        #Arrange
        created = date.today() + timedelta(days=10)
        accessed = date.today() + timedelta(days=10)
        modfied = date.today() + timedelta(days=10)

        fs.makedir("dir")
        fs.wrapped_fs.getinfo = Mock(return_value={
            "created_time": created,
            "modified_time": accessed,
            "accessed_time": modfied})
        #Act
        info = fs.getinfo("dir")
        #Assert
        assert info["created_time"] == created
        assert info["modified_time"] == accessed
        assert info["accessed_time"] == modfied

    def test_getinfo_returns_latest_times(self, fs_with_test_file):
        #Arrange
        created_max = date.today() + timedelta(days=10)
        accessed_max = date.today() + timedelta(days=10)
        modfied_max = date.today() + timedelta(days=10)

        def getinfo_patch(path):
            if path == "backup.tar.part0":
                return {"created_time": created_max, "modified_time": date.today(), "accessed_time": accessed_max}
            else:
                return {"created_time": date.today(), "modified_time": modfied_max, "accessed_time": date.today()}

        fs_with_test_file.wrapped_fs.getinfo = getinfo_patch
        fs_with_test_file.getsize = lambda p: kb(7)
        #Act
        info = fs_with_test_file.getinfo("backup.tar")
        #Assert
        assert info["created_time"] == created_max
        assert info["accessed_time"] == accessed_max
        assert info["modified_time"] == modfied_max

    def test_getinfo_returns_info_of_parts(self, fs_with_test_file):
        #Act
        info = fs_with_test_file.getinfo("backup.tar")
        part_infos = info['parts']
        #Assert
        assert len(part_infos) == 2

    def test_getinfo_returns_correct_size(self, fs_with_test_file):
        #Act
        info = fs_with_test_file.getinfo("backup.tar")
        #Assert
        assert info["size"] == kb(8)

    def test_copy_raises_error_if_not_exists(self, fs):
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.getinfo("copy_me_if_you_can")

    def test_copy_copies_the_parts(self, fs_with_test_file):
        #Arrange
        fs_with_test_file.makedir("copy_folder")
        fs_with_test_file.wrapped_fs.copy = Mock()
        #Act
        fs_with_test_file.copy("backup.tar", "copy_folder/backup.tar")
        #Assert
        fs_with_test_file.wrapped_fs.copy.assert_has_calls([
                                                               call("backup.tar.part0", "copy_folder/backup.tar.part0"),
                                                               call("backup.tar.part1",
                                                                    "copy_folder/backup.tar.part1")], any_order=True)


class TestPartedFile(object):
    @fixture
    def parted_file(self):
        fs = MemoryFS()
        mode = "wb+"
        path = "cuckoo.tar"
        parts = [FilePart(fs.open("cuckoo.tar.part0", mode)), FilePart(fs.open("cuckoo.tar.part1", mode))]
        return PartedFile(path=path, mode=mode, fs=fs, max_part_size=kb(4), parts=parts)

    def test_current_part_returns_first_part_when_file_pointer_is_zero(self, parted_file):
        #Arrange
        parted_file._file_pointer = 0
        #Act & Assert
        assert parted_file.current_part == parted_file.parts[0]

    def test_current_part_returns_last_part_when_file_pointer_is_max_part_size(self, parted_file):
        #Arrange
        parted_file._file_pointer = kb(4)
        #Act & Assert
        assert parted_file.current_part == parted_file.parts[1]

    def test_current_part_raises_error_when_file_pointer_is_bigger_than_parts(self, parted_file):
        #Arrange
        parted_file._mode = "r"
        parted_file._file_pointer = 4 * kb(4)
        #Act & Assert
        with raises(InvalidFilePointerLocation):
            _ = parted_file.current_part

    def test_write_returns_none_if_all_data_could_be_written(self, parted_file):
        #Act
        unwritten_data = parted_file._write(urandom(kb(4)))
        #Assert
        assert unwritten_data is None

    def test_write_returns_data_that_is_bigger_than_max_part_size(self, parted_file):
        #Act
        unwritten_data = parted_file._write(urandom(kb(5)))
        #Assert
        assert len(unwritten_data) == kb(1)

    def test_write_with_flushing_mode_calls_itself_until_all_data_is_written(self, parted_file):
        #Act
        unwritten_data = parted_file._write(urandom(kb(5)), flushing=True)
        #Assert
        assert unwritten_data is None

    def test_write_sets_file_pointer_to_next_free_position(self, parted_file):
        #Act
        parted_file._write(urandom(kb(4)))
        #Assert
        assert parted_file._file_pointer == kb(4)

    def test_write_big_amount_expands_to_parts(self, parted_file):
        #Act
        parted_file._write(urandom(kb(12)), flushing=True)
        #Assert
        assert len(parted_file.parts) == 3

    def test_seek_absolute_should_set_filepointer_to_offset(self, parted_file):
        #Arrange
        parted_file._file_pointer = kb(1)
        #Act
        parted_file._seek(offset=kb(0), whence=0)
        #Assert
        assert parted_file._file_pointer == kb(0)

    def test_seek_goes_to_current_part_and_sets_other_parts_to_start(self, parted_file):
        #Arrange
        parted_file.parts[0].seek = Mock()
        parted_file.parts[1].seek = Mock()
        #Act
        parted_file._seek(offset=kb(5), whence=0)
        #Assert
        parted_file.parts[0].seek.assert_called_once_with(kb(0), 0)
        parted_file.parts[1].seek.assert_called_once_with(kb(1), 0)


    def test_seek_relative_should_add_ofset_to_filepointer(self, parted_file):
        #Arrange
        parted_file._file_pointer = kb(1)
        #Act
        parted_file._seek(offset=kb(1), whence=1)
        #Assert
        assert parted_file._file_pointer == kb(2)

    @mark.xfail
    def test_seek_relative_to_end_should_set_filepointer_to_last_part(self, parted_file):
        #Act
        parted_file._seek(offset=-kb(4), whence=2)
        #Assert
        assert parted_file._file_pointer == kb(4)

    def test_tell_returns_file_pointer(self, parted_file):
        #Arrange
        parted_file._file_pointer = kb(2)
        #Act
        pos = parted_file._tell()
        #Assert
        assert pos == kb(2)

    def test_read_returns_data_from_current_part_and_calls_itself_for_next_part(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(5)), flushing=True)
        parted_file._seek(offset=kb(3), whence=0)
        #Act
        read_data = parted_file._read()
        #Assert
        assert len(read_data) == kb(2)

    def test_read_returns_data_from_current_part_in_chunks(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(5)), flushing=True)
        parted_file._seek(offset=kb(3), whence=0)
        #Act
        chunk1 = parted_file._read(kb(1))
        chunk2 = parted_file._read(kb(1))
        #Assert
        assert len(chunk1) == kb(1)
        assert len(chunk2) == kb(1)

    def test_read_returns_only_data_of_current_part_with_bigger_sizehint(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(5)), flushing=True)
        parted_file._seek(offset=kb(3), whence=0)
        #Act
        chunk = parted_file._read(kb(2))
        #Assert
        assert len(chunk) == kb(1)

    def test_read_returns_none_after_read_all(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(5)), flushing=True)
        parted_file._seek(offset=0, whence=0)
        parted_file._read()
        #Act
        eof = parted_file._read()
        #Assert
        assert eof is None

    def test_read_as_chunks_returns_none_at_end_of_file(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(5)), flushing=True)
        parted_file._seek(offset=kb(4), whence=0)
        parted_file._read(kb(1))
        #Act
        eof = parted_file._read(kb(1))
        #Assert
        assert eof is None

    def test_close_calls_super_for_flush_and_closes_all_parts(self, parted_file):
        #Arrange
        parted_file._write(urandom(kb(4)))
        parted_file.parts[0].close = Mock()
        parted_file.parts[1].close = Mock()
        #Act
        parted_file.close()
        #Assert
        parted_file.parts[0].close.assert_called_with()
        parted_file.parts[1].close.assert_called_with()