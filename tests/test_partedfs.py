# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os import urandom

from mock import Mock, call

from pytest import fixture, raises, mark

from fs.memoryfs import MemoryFS

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

    def test_encode_should_return_file_with_part0_extension(self, fs):
        #Arrange
        path = "backup.tar"
        #Act
        encoded_path = fs._encode(path)
        #Assert
        assert encoded_path == "backup.tar.part0"

    def test_decode_should_return_part_without_part_extension(self, fs):
        #Arrange
        encoded_path = "backup.tar.part1"
        #Act
        decoded_path = fs._decode(encoded_path)
        #Assert
        assert decoded_path == "backup.tar"

    def test_listparts_returns_all_parts_for_a_path(self, fs):
        #Arrange
        path = "backup.tar"
        fs.wrapped_fs.setcontents("backup.tar.part0", data=urandom(kb(4)))
        fs.wrapped_fs.setcontents("backup.tar.part1", data=urandom(kb(4)))
        #Act
        listing = fs.listparts(path)
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