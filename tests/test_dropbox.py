# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from pytest import fixture

from dropbox.client import DropboxClient

from drive.providers.dropbox import DropboxFS
from tests.test_fs import FSTestBase


class TestDropboxFS(FSTestBase):
    """Integration test of the DropboxFS using a real dropbox folder"""
    @fixture
    def fs(self, request):
        """Create a DropboxFS with a real Dropbox client that connects to a
        test directory. The fixture deletes all the created
        folders and folders in the finalizer"""
        client = DropboxClient('q3UFckbQggcAAAAAAAAAAdj9VvMFNx18Et2_BZLZxxLxCg6BLu3fLa15m8-qBvpB')
        fs = DropboxFS(client)

        def cleanup_dropbox():
            for file_path in fs.listdir(files_only=True):
                fs.remove(file_path)
            for dir in fs.listdir(dirs_only=True):
                fs.removedir(dir)

        request.addfinalizer(cleanup_dropbox)
        return fs

    def test_desc_returns_storage_name_and_path(self, fs):
        #Arrange
        path = "hello_i_am_mr_folder"
        #Act
        desc = fs.desc(path)
        #Assert
        assert desc == path + " in Dropbox"
