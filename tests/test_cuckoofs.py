# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from fs.base import FS
from fs.path import normpath
from pytest import fixture

from dropbox.client import DropboxClient
from fs.errors import ResourceNotFoundError, ResourceInvalidError, DestinationExistsError

from drive.providers.dropbox import DropboxFS
from tests.test_fs import FSTestBase


class CuckooFS(FS):
    """
    Writes to many underlying storage providers implemented as remote filesystems.
    """
    _meta = {
        "network": True,
        "virtual": True,
        "read_only": False,
        "unicode_paths": True,
        "case_insensitive_paths": False,
        "atomic.move": True,
        "atomic.copy": True,
        "atomic.makedir": True,
        "atomic.rename": True,
        "atomic.setcontents": True,
        "file.read_and_write": False,
    }

    def __str__(self):
        return "<CuckooFS: {0}>".format(self.root_path)

    # --------------------------------------------------------------------
    # Essential Methods as defined in
    # https://pythonhosted.org/fs/implementersguide.html#essential-methods
    # --------------------------------------------------------------------
    @synchronize
    def open(self, path, mode="rb", **kwargs):
        path = normpath(path).lstrip('/')

        if "r" in mode:
            if not self.exists(path):
                raise ResourceNotFoundError(path)
            if self.isdir(path):
                raise ResourceInvalidError(path)
        file = DropboxFile(self, path, mode)
        return file

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
