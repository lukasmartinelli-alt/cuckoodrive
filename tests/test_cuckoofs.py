# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from fs.base import FS
from pytest import fixture

from dropbox.client import DropboxClient
from fs.errors import ResourceNotFoundError, ResourceInvalidError, DestinationExistsError

from drive.providers.dropbox import DropboxFS
from tests.test_fs import FSTestBase


class CuckooFS(FS):
    # ------------------------------------------------------------------------
    # Non-Essential Methods as defined in
    # https://pythonhosted.org/fs/implementersguide.html#non-essential-methods
    # ------------------------------------------------------------------------

    def desc(self, path):
        return "%s in CuckooDrive" % path


# noinspection PyMethodMayBeStatic
class TestCuckooFS(FSTestBase):
    """Integration test of the DropboxFS using a real dropbox folder"""

    @fixture
    def fs(self, request):
        fs = CuckooFS()
        return fs

    def test_desc_returns_storage_name_and_path(self, fs):
        #Arrange
        path = "hello_i_am_mr_folder"
        #Act
        desc = fs.desc(path)
        #Assert
        assert desc == path + " in CuckooDrive"
