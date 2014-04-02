# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import unittest
from fs.tests import FSTestCases
from fs.wrapfs.limitsizefs import LimitSizeFS
from mock import Mock

from pytest import fixture, raises, mark

from fs.errors import NoMetaError
from fs.memoryfs import MemoryFS

from drive.multifs import WritableMultiFS, free_space
from drive.utils import mb


class TestExternalWritableMultiFS(unittest.TestCase, FSTestCases):
    def setUp(self):
        multifs = WritableMultiFS()
        fs1 = LimitSizeFS(MemoryFS(), mb(230))
        fs2 = LimitSizeFS(MemoryFS(), mb(300))

        multifs.addfs("fs1", fs1)
        multifs.addfs("fs2", fs2)

        self.fs = multifs

    def tearDown(self):
        self.fs.close()

    @mark.xfail(reason="Combination of LimitSizeFS and MultiFS does not work properly")
    def test_listdir(self):
        super(TestExternalWritableMultiFS, self).test_listdir()

    @mark.xfail(reason="Combination of LimitSizeFS and MultiFS does not work properly")
    def test_listdirinfo(self):
        super(TestExternalWritableMultiFS, self).test_listdirinfo()

    @mark.xfail(reason="Combination of LimitSizeFS and MultiFS does not work properly")
    def test_open_on_directory(self):
        super(TestExternalWritableMultiFS, self).test_open_on_directory()

    @mark.xfail(reason="Combination of LimitSizeFS and MultiFS does not work properly")
    def test_remove(self):
        super(TestExternalWritableMultiFS, self).test_remove()


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

    def test_free_space_returns_meta_if_has_meta(self):
        #Arrange
        fs = MemoryFS()
        fs.getmeta = Mock(return_value=mb(230))
        #Act
        space = free_space(fs)
        #Assert
        assert space == mb(230)

    def test_free_space_returns_cur_size_if_is_limitsizefs(self):
        #Arrange
        fs = LimitSizeFS(MemoryFS(), mb(230))
        #Act
        space = free_space(fs)
        #Assert
        assert space == mb(230)

    def test_free_space_raises_meta_error_if_no_size_info(self):
        #Arrange
        fs = MemoryFS()
        #Act & Assert
        with raises(NoMetaError):
            free_space(fs)

    def test_writefs_returns_fs_with_most_free_space(self, fs):
        #Act & Assert
        assert fs.writefs == fs.fs_lookup["fs1"]

    def test_writefs_returns_none_if_no_fs(self):
        #Arrange
        multifs = WritableMultiFS()
        #Act & Assert
        assert multifs.writefs is None

    def test_writefs_returns_none_if_all_fs_closed(self):
        #Arrange
        multifs = WritableMultiFS()
        fs1 = MemoryFS()
        multifs.addfs("fs1", fs1)
        fs1.close()
        #Act
        assert multifs.writefs is None

    def test_set_writefs_raises_error_if_value_not_none(self):
        #Arrange
        multifs = WritableMultiFS()
        #Act & Assert
        with raises(AttributeError):
            multifs.writefs = MemoryFS()