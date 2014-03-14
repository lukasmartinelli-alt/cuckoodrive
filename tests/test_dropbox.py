# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os import urandom
from pytest import fixture, raises


from dropbox.client import DropboxClient
from fs.errors import ResourceNotFoundError, ResourceInvalidError

from drive.providers.dropbox import DropboxFS


class TestDropboxFs:
    """Integration test of the DropboxFS using a real dropbox folder"""
    @fixture
    def fs(self, request):
        """Create a DropboxFS with a real Dropbox client that connects to a
        test directory. The fixture deletes all the created
        folders and folders in the finalizer"""
        client = DropboxClient('fIeCAUcoJUcAAAAAAAAAAYgZtfWLP7e1U8c8rbkEOCkrXXUU9WshRiufV8TY-dfy')
        fs = DropboxFS(client)

        def cleanup_dropbox():
            for file_path in fs.listdir(files_only=True):
                fs.remove(file_path)
            for dir in fs.listdir(dirs_only=True):
                fs.removedir(dir)

        request.addfinalizer(cleanup_dropbox)
        return fs

    @fixture
    def folder_structure(self, fs):
        dir_paths = ["dir1", "dir2", "dir3"]
        file_paths = ["file1.txt", "file2.txt"]
        for path in dir_paths:
            fs.makedir(path)
        for path in file_paths:
            with fs.open(path, "w") as file:
                file.write(str(urandom(1024)))
        return (dir_paths, file_paths)

    def test_open_file_that_is_a_dir_raises_error(self, fs):
        #Arrange
        path = "im_a_dir_and_not_a_file"
        fs.makedir(path)
        #Act & Assert
        with raises(ResourceInvalidError):
            fs.open(path)

    def test_open_file_that_doesnt_exist(self, fs):
        #Arrange
        path = "get_me_if_you_can"
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.open(path)

    def test_open_existing_file_and_read_from_it(self, fs):
        #Arrange
        path = "new_file"
        text = "Lorem ipsum"
        with fs.open(path, "w") as file:
            file.write(text)
        #Act
        written_text = ""
        with fs.open(path, "r") as file:
            written_text = file.read()
        #Assert
        assert text == written_text

    def test_open_new_file_as_binary_and_write_to_it(self, fs):
        #Arrange
        path = "new_binary_file"
        #Act
        file = fs.open(path, "wb")
        file.write(urandom(1024))
        file.close()
        #Assert
        assert fs.exists(path)

    def test_open_new_file_as_text_and_write_to_it(self, fs):
        #Arrange
        path = "new_text_file"
        #Act
        with fs.open(path, "w") as file:
            file.write(str(urandom(1024)))
        #Assert
        assert fs.exists(path)

    def test_listdir_lists_only_directories(self, fs, folder_structure):
        #Arrange
        dir_paths, file_paths = folder_structure
        #Act
        listing = fs.listdir("/", dirs_only=True)
        #Assert
        assert listing == dir_paths

    def test_listdir_lists_only_files(self, fs, folder_structure):
        #Arrange
        dir_paths, file_paths = folder_structure
        #Act
        listing = fs.listdir("/", files_only=True)
        #Assert
        assert listing == file_paths

    def test_listdir_lists_all_existing_directories(self, fs, folder_structure):
        #Arrange
        dir_paths, file_paths = folder_structure
        #Act
        listing = fs.listdir("/")
        #Assert
        assert listing == dir_paths + file_paths

    def test_isdir_returns_true_if_it_is_an_existing_directory(self, fs):
        #Arrange
        path = "i_am_a_directory"
        fs.makedir(path)
        #Act
        result = fs.isdir(path)
        #Assert
        assert result

    def test_isfile_returns_true_if_isdir_is_false(self, fs):
        #Arrange
        fs.isdir = lambda path: False
        #Act
        result = fs.isfile("file.txt")
        #Assert
        assert result

    def test_makedir_creates_directory(self, fs):
        #Arrange
        path = "testdir"
        #Act
        fs.makedir(path)
        #Assert
        assert fs.exists(path)

    def test_removedir_deletes_directory(self, fs):
        #Arrange
        path = "deletme"
        fs.makedir(path)
        #Act
        fs.removedir(path)
        #Assert
        assert not fs.exists(path)

    def test_removedir_raises_resourcenotfound_exception_when_dir_doesnt_exist(self, fs):
        #Arrange
        path = "remove_me_if_you_can"
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.removedir(path)

    def test_exists_returns_false_if_file_was_deleted(self, fs):
        #Arrange
        path = "i_shouldnt_exist_afterwards"
        fs.makedir(path)
        fs.removedir(path)
        #Act
        exists = fs.exists(path)
        #Assert
        assert not exists

    def test_getinfo_raises_resourcenotfound_exception_when_path_doesnt_exist(self, fs):
        #Arrange
        path = "i_dont_exist"
        #Act & Assert
        with raises(ResourceNotFoundError):
            fs.getinfo(path)

    def test_desc_returns_storage_name_and_path(self, fs):
        #Arrange
        path = "hello_i_am_mr_folder"
        #Act
        desc = fs.desc(path)
        #Assert
        desc == path + " in Dropbox"
