# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os import urandom
from pytest import fixture, raises


from dropbox.client import DropboxClient
from fs.errors import ResourceNotFoundError

from drive.providers.dropbox import DropboxFS


class TestDropboxFs:
    """Integration test of the DropboxFS using a real dropbox folder"""
    @fixture
    def dropbox(self, request):
        """Create a real dropbox client that connects to a test directory. The fixture
        deletes all the created folders in the finalizer"""
        client = DropboxClient('fIeCAUcoJUcAAAAAAAAAAYgZtfWLP7e1U8c8rbkEOCkrXXUU9WshRiufV8TY-dfy')
        fs = DropboxFS(client)

        def cleanup_dropbox():
            for dir in fs.listdir():
                fs.removedir(dir)

        request.addfinalizer(cleanup_dropbox)
        return fs

    def test_open_file_that_doesnt_exist(self, dropbox):
        #Arrange
        path = "get_me_if_you_can"
        #Act & Assert
        with raises(ResourceNotFoundError):
            dropbox.open(path)

    def test_open_existing_file_and_read_from_it(self, dropbox):
        #Arrange
        path = "new_file"
        text = "Lorem ipsum"
        with dropbox.open(path, "w") as file:
            file.write(text)
        #Act
        written_text = ""
        with dropbox.open(path, "r") as file:
            written_text = file.read()
        #Assert
        assert text == written_text

    def test_open_new_file_as_binary_and_write_to_it(self, dropbox):
        #Arrange
        path = "new_binary_file"
        #Act
        file = dropbox.open(path, "wb")
        file.write(urandom(1024))
        file.close()
        #Assert
        assert dropbox.exists(path)

    def test_open_new_file_as_text_and_write_to_it(self, dropbox):
        #Arrange
        path = "new_text_file"
        #Act
        with dropbox.open(path, "w") as file:
            file.write(str(urandom(1024)))
        #Assert
        assert dropbox.exists(path)

    def test_listdir_lists_all_existing_directories(self, dropbox):
        #Arrange
        paths = ["dir1", "dir2", "dir3"]
        for path in paths:
            dropbox.makedir(path)
        #Act
        listing = dropbox.listdir("/")
        #Assert
        assert listing == paths

    def test_isdir_returns_true_if_it_is_an_existing_directory(self, dropbox):
        #Arrange
        path = "i_am_a_directory"
        dropbox.makedir(path)
        #Act
        result = dropbox.isdir(path)
        #Assert
        assert result

    def test_isfile_returns_true_if_isdir_is_false(self, dropbox):
        #Arrange
        dropbox.isdir = lambda path: False
        #Act
        result = dropbox.isfile("file.txt")
        #Assert
        assert result

    def test_makedir_creates_directory_in_dropbox(self, dropbox):
        #Arrange
        path = "testdir"
        #Act
        dropbox.makedir(path)
        #Assert
        assert dropbox.exists(path)

    def test_removedir_deletes_directory(self, dropbox):
        #Arrange
        path = "deletme"
        dropbox.makedir(path)
        #Act
        dropbox.removedir(path)
        #Assert
        assert not dropbox.exists(path)

    def test_removedir_raises_resourcenotfound_exception_when_dir_doesnt_exist(self, dropbox):
        #Arrange
        path = "remove_me_if_you_can"
        #Act & Assert
        with raises(ResourceNotFoundError):
            dropbox.removedir(path)

    def test_exists_returns_false_if_file_was_deleted(self, dropbox):
        #Arrange
        path = "i_shouldnt_exist_afterwards"
        dropbox.makedir(path)
        dropbox.removedir(path)
        #Act
        exists = dropbox.exists(path)
        #Assert
        assert not exists

    def test_getinfo_raises_resourcenotfound_exception_when_path_doesnt_exist(self, dropbox):
        #Arrange
        path = "i_dont_exist"
        #Act & Assert
        with raises(ResourceNotFoundError):
            dropbox.getinfo(path)

    def test_desc_returns_storage_name_and_path(self, dropbox):
        #Arrange
        path = "hello_i_am_mr_folder"
        #Act
        desc = dropbox.desc(path)
        #Assert
        desc == path + " in Dropbox"
