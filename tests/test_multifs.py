# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from os import urandom

import unittest
from mock import Mock
from pytest import fixture, raises

from fs.tests import FSTestCases
from fs.wrapfs.limitsizefs import LimitSizeFS
from fs.errors import NoMetaError
from fs.memoryfs import MemoryFS

from cuckoodrive.multifs import WritableMultiFS, free_space
from cuckoodrive.utils import mb, kb


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


class TestWritableMultiFS(object):

    @fixture
    def fs(self):
        multifs = WritableMultiFS()

        fs1 = LimitSizeFS(MemoryFS(), mb(300))
        fs2 = LimitSizeFS(MemoryFS(), mb(240))

        multifs.addfs("fs1", fs1)
        multifs.addfs("fs2", fs2)

        return multifs

    def test_free_space_returns_meta_if_has_meta(self):
        # Arrange
        fs = MemoryFS()
        fs.getmeta = Mock(return_value=mb(230))
        # Act
        space = free_space(fs)
        # Assert
        assert space == mb(230)

    def test_free_space_returns_cur_size_if_is_limitsizefs(self):
        # Arrange
        fs = LimitSizeFS(MemoryFS(), mb(230))
        # Act
        space = free_space(fs)
        # Assert
        assert space == mb(230)

    def test_free_space_raises_meta_error_if_no_size_info(self):
        # Arrange
        fs = MemoryFS()
        # Act & Assert
        with raises(NoMetaError):
            free_space(fs)

    def test_writefs_returns_fs_with_most_free_space(self, fs):
        # Act & Assert
        assert fs.writefs == fs.fs_lookup["fs1"]

    def test_writefs_returns_none_if_no_fs(self):
        # Arrange
        multifs = WritableMultiFS()
        # Act & Assert
        assert multifs.writefs is None

    def test_writefs_returns_none_if_all_fs_closed(self):
        # Arrange
        multifs = WritableMultiFS()
        fs1 = MemoryFS()
        multifs.addfs("fs1", fs1)
        fs1.close()
        # Act
        assert multifs.writefs is None

    def test_set_writefs_raises_error_if_value_not_none(self):
        # Arrange
        multifs = WritableMultiFS()
        # Act & Assert
        with raises(AttributeError):
            multifs.writefs = MemoryFS()

    def test_open_switches_writefs_to_location_of_existing_file(self, fs):
        # Arrange
        fs.fs_lookup["fs1"].setcontents("backup.tar.part0", data=urandom(kb(4)))
        fs.fs_lookup["fs2"].setcontents("backup.tar.part1", data=urandom(kb(3)))

        # Act
        with fs.open("backup.tar.part0", mode="r+b") as fh:
            fh.write(urandom(kb(5)))

        with fs.open("backup.tar.part1", mode="r+b") as fh:
            fh.write(urandom(kb(2)))

        # Assert
        assert fs.getsize("backup.tar.part0") == kb(5)
        assert fs.getsize("backup.tar.part1") == kb(3)

    def test_remove_switches_writefs_to_location_of_existing_file(self, fs):
        # Arrange
        fs.fs_lookup["fs1"].setcontents("backup.tar.part0", data=urandom(kb(4)))
        fs.fs_lookup["fs2"].setcontents("backup.tar.part1", data=urandom(kb(3)))

        # Act
        fs.remove("backup.tar.part0")
        fs.remove("backup.tar.part1")

        # Assert
        assert not fs.exists("backup.tar.part0")
        assert not fs.exists("backup.tar.part1")
