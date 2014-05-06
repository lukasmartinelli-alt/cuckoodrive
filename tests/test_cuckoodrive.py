# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import unittest
import tempfile
import shutil
import os

from pytest import fixture, mark

from fs.tests import FSTestCases
from fs.wrapfs.limitsizefs import LimitSizeFS
from fs.memoryfs import MemoryFS
from fs.osfs import OSFS

from cuckoodrive import MountedCuckooDrive, CuckooDriveFS
from cuckoodrive.utils import mb


class TestMountedCuckooDrive(object):
    """Tests of this kind could be used as benchmarks"""
    @fixture
    def mount_drive(self, request):
        fs1_dir = tempfile.mkdtemp()
        fs2_dir = tempfile.mkdtemp()

        drive = MountedCuckooDrive(path=tempfile.mkdtemp(), remote_uris=[fs1_dir, fs2_dir])
        drive.mount()

        def cleanup():
            drive.unmount()
            shutil.rmtree(fs1_dir)
            shutil.rmtree(fs2_dir)

        request.addfinalizer(cleanup)

        return drive

    @fixture
    def mounted_fs(self, mount_drive):
        return OSFS(mount_drive.path)

    @fixture
    def user_fs(self, request):
        user_dir = tempfile.mkdtemp()

        fs = OSFS(user_dir)
        request.addfinalizer(lambda: shutil.rmtree(user_dir))
        return fs

    def test_copy_large_file(self, user_fs, mounted_fs):
        # Arrange
        data = os.urandom(mb(43))
        user_fs.setcontents("backup.tar", data)
        src = user_fs.getsyspath("backup.tar")
        dst = os.path.join(mounted_fs.root_path, "backup.tar")
        # Act
        shutil.copyfile(src, dst)
        # Assert
        assert data == mounted_fs.getcontents("backup.tar")


class TestCuckooDriveFS(object):
    @fixture
    def fs(self, request):
        fs1 = LimitSizeFS(MemoryFS(), mb(300))
        fs2 = LimitSizeFS(MemoryFS(), mb(300))
        fs = CuckooDriveFS([fs1, fs2])
        request.addfinalizer(lambda: fs.close())
        return fs

    # Special integration tests


class TestExternalCuckooDriveFS(unittest.TestCase, FSTestCases):
    def setUp(self):
        fs1 = LimitSizeFS(MemoryFS(), mb(300))
        fs2 = LimitSizeFS(MemoryFS(), mb(300))
        self.fs = CuckooDriveFS([fs1, fs2])

    def tearDown(self):
        self.fs.close()

    @mark.xfail(reason="Appending does not work yet")
    def test_readwriteappendseek(self):
        super(TestExternalCuckooDriveFS, self).test_readwriteappendseek()

    @mark.xfail(reason="FS is not truncatable")
    def test_truncate_to_larger_size(self):
        super(TestExternalCuckooDriveFS, self).test_truncate_to_larger_size()

    @mark.xfail(reason="FS is not truncatable")
    def test_truncate(self):
        super(TestExternalCuckooDriveFS, self).test_truncate()
