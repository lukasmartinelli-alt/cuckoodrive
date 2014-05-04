# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import unittest
from pytest import fixture

from fs.tests import FSTestCases
from fs.wrapfs.limitsizefs import LimitSizeFS
from fs.memoryfs import MemoryFS

from cuckoodrive import CuckooDrive, CuckooDriveFS
from cuckoodrive.utils import mb


class TestCuckooDrive(object):
    @fixture
    def fs(self, request):
        fs1 = LimitSizeFS(MemoryFS(), mb(230))
        fs2 = LimitSizeFS(MemoryFS(), mb(300))
        return CuckooDrive("/", [fs1, fs2])

    def test_copy_large_files_around():
        pass


class TestExternalCuckooDriveFS(unittest.TestCase, FSTestCases):
    def setUp(self):
        fs1 = LimitSizeFS(MemoryFS(), mb(230))
        fs2 = LimitSizeFS(MemoryFS(), mb(300))
        self.fs = CuckooDriveFS([fs1, fs2])

    def tearDown(self):
        self.fs.close()
