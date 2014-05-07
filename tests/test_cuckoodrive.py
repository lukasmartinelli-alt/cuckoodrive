# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import unittest

from pytest import fixture, mark

from fs.tests import FSTestCases
from fs.wrapfs.limitsizefs import LimitSizeFS
from fs.memoryfs import MemoryFS

from cuckoodrive import CuckooDriveFS
from cuckoodrive.utils import mb


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
