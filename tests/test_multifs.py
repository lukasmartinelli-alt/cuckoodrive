# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from mock import Mock

from pytest import fixture

from fs.errors import NoMetaError
from fs.memoryfs import MemoryFS

from drive.multifs import WritableMultiFS
from drive.utils import mb


class TestWritableMultiFS(object):

    @fixture
    def fs(self):
        multifs = WritableMultiFS()
        fs1 = MemoryFS()
        fs2 = MemoryFS()

        def getmeta_fs1(meta_name):
            if meta_name == "free_space":
                return mb(300)
            raise NoMetaError(meta_name)

        def getmeta_fs2(meta_name):
            if meta_name == "free_space":
                return mb(240)
            raise NoMetaError(meta_name)

        fs1.getmeta = getmeta_fs1
        fs2.getmeta = getmeta_fs2

        multifs.addfs("fs1", fs1)
        multifs.addfs("fs2", fs2)

        return multifs

    def test_best_writefs_returns_fs_with_most_free_space(self, fs):
        #Act & Assert
        assert fs.best_writefs() == fs.fs_lookup["fs1"]

    def test_open_sets_best_writfs_as_new_writefs_for_write_mode(self, fs):
        #Arrange
        path = "backup.tar"
        fs.best_writefs = lambda: fs.fs_lookup["fs1"]
        #Act
        fs.open(path, mode="w")
        #Assert
        assert fs.writefs == fs.best_writefs()