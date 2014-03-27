# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os import urandom
from datetime import datetime, timedelta, date
from fs.path import pathcombine

from mock import Mock, call
from pytest import fixture, raises, mark

from fs.memoryfs import MemoryFS
from fs.errors import ResourceNotFoundError, ResourceInvalidError

from drive.partedfs import PartedFS
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
                                                  call("backup.tar.part1", "backup2.tar.part1")], any_order=True)

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
                                                  call("backup.tar.part1", "copy_folder/backup.tar.part1")], any_order=True)

