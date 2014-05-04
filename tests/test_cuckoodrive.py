# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import unittest
import tempfile
import shutil

from pytest import fixture

from fs.tests import FSTestCases
from fs.wrapfs.limitsizefs import LimitSizeFS
from fs.memoryfs import MemoryFS
from fs.osfs import OSFS

from cuckoodrive import MountedCuckooDrive, CuckooDriveFS
from cuckoodrive.utils import mb


class TestMountedCuckooDrive(object):
    @fixture
    def mount_drive(self, request):
        fs1_dir = tempfile.mkdtemp()
        fs2_dir = tempfile.mkdtemp()

        drive = MountedCuckooDrive(path=tempfile.mkdtemp(), remote_uris=[fs1_dir, fs2_dir])

        def cleanup():
            drive.unmount()
            shutil.rmtree(fs1_dir)
            shutil.rmtree(fs2_dir)

        request.addfinalizer(cleanup)

        return drive

    @fixture
    def user_fs(self, request):
        user_dir = tempfile.mkdtemp()

        fs = OSFS(user_dir)
        request.addfinalizer(lambda: shutil.user_dir)
        return fs

    def test_copy_large_file(self):
        pass


class TestExternalCuckooDriveFS(unittest.TestCase, FSTestCases):
    def setUp(self):
        fs1 = LimitSizeFS(MemoryFS(), mb(300))
        fs2 = LimitSizeFS(MemoryFS(), mb(300))
        self.fs = CuckooDriveFS([fs1, fs2])

    def tearDown(self):
        self.fs.close()
