# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from os import urandom
from datetime import datetime, timedelta

import unittest

from pytest import fixture, mark
from mock import Mock

from fs.tests import FSTestCases
from fs.wrapfs.limitsizefs import LimitSizeFS
from fs.memoryfs import MemoryFS
from fs.tempfs import TempFS
from fs.watch import EVENT

from cuckoodrive import CuckooDriveFS, SyncedCuckooDrive
from cuckoodrive.utils import mb, kb


class TestCuckooDriveFS(object):
    @fixture
    def fs(self, request):
        fs1 = LimitSizeFS(MemoryFS(), mb(300))
        fs2 = LimitSizeFS(MemoryFS(), mb(300))
        fs = CuckooDriveFS([fs1, fs2])
        request.addfinalizer(lambda: fs.close())
        return fs

    # Special integration tests


class TestSyncedCuckooDrive(object):
    @fixture
    def filesystems(self):
        userfs = TempFS()
        fs1 = LimitSizeFS(MemoryFS(), mb(300))
        fs2 = LimitSizeFS(MemoryFS(), mb(300))
        remotefs = CuckooDriveFS(remote_filesystems=[fs1, fs2])
        return (userfs, remotefs)

    @fixture
    def drive(self, filesystems):
        userfs, remotefs = filesystems
        return SyncedCuckooDrive(userfs, remotefs)

    def test_register_callback_if_watch_specified(self, filesystems):
        # Arrange
        userfs, remotefs = filesystems
        userfs.add_watcher = Mock()
        # Act
        drive = SyncedCuckooDrive(userfs, remotefs, watch=True)
        # Assert
        userfs.add_watcher.assert_called_with(drive.userfs_changed)

    def test_initial_synchronization_is_made(self, filesystems, monkeypatch):
        # Arrange
        userfs, remotefs = filesystems
        userfs.add_watcher = Mock()
        monkeypatch.setattr(SyncedCuckooDrive, 'sync_dirs', Mock())
        monkeypatch.setattr(SyncedCuckooDrive, 'sync_files', Mock())
        # Act
        drive = SyncedCuckooDrive(userfs, remotefs)
        # Arrange
        assert drive.sync_dirs.called
        assert drive.sync_files.called

    def test_userfs_create_event_message_crafts_info_message(self, drive):
        # Arrange
        event = EVENT(drive.userfs, "backup.tar")
        # Act
        message = drive.create_event_message(event)
        # Assert
        assert message == "    event /backup.tar"

    def test_userfs_changed_invokes_synchronization(self, filesystems, monkeypatch):
        # Arrange
        userfs, remotefs = filesystems
        monkeypatch.setattr(SyncedCuckooDrive, 'sync_dirs', Mock())
        monkeypatch.setattr(SyncedCuckooDrive, 'sync_files', Mock())
        drive = SyncedCuckooDrive(userfs, remotefs, watch=True)
        # Act
        drive.userfs.setcontents("newfile.txt", "Sync me if you can!")
        # Arrange
        assert drive.sync_dirs.called
        assert drive.sync_files.called

    def test_sync_dirs_copies_only_not_existing_dirs(self, drive):
        # Arrange
        drive.userfs.makedir("synced")
        drive.userfs.setcontents("synced/newfile.txt", urandom(kb(1)))

        drive.remotefs.makedir("notsynced")
        drive.userfs.makedir("notsynced")
        drive.userfs.setcontents("notsynced/oldfile.txt", urandom(kb(2)))
        # Act
        drive.sync_dirs()
        # Arrange
        assert drive.remotefs.exists("synced/newfile.txt")
        assert not drive.remotefs.exists("notsynced/oldfile.txt")

    def test_sync_files_copies_file_if_it_only_exists_on_userfs(self, drive):
        # Arrange
        drive.userfs.setcontents("newfile.txt", urandom(kb(1)))

        drive.remotefs.setcontents("oldfile.txt", urandom(kb(1)))
        drive.userfs.setcontents("oldfile.txt", urandom(kb(2)))
        # Act
        drive.sync_files()
        # Arrange
        assert drive.remotefs.exists("newfile.txt")
        assert drive.remotefs.getsize("oldfile.txt") == kb(2)

    def test_has_conflict_returns_true_if_destination_is_newer(self, drive):
        # Arrange
        drive.userfs.setcontents("source.txt", urandom(kb(1)))
        drive.userfs.settimes("source.txt", modified_time=datetime.today() - timedelta(days=1))

        drive.remotefs.setcontents("dest.txt", urandom(kb(2)))
        drive.remotefs.settimes("dest.txt", modified_time=datetime.today())
        # Act
        conflict = drive.has_conflict(src="source.txt", dst="dest.txt")
        # Assert
        assert conflict

    def test_has_conflict_returns_false_if_source_is_newer(self, drive):
        # Arrange
        drive.userfs.setcontents("source.txt", urandom(kb(1)))
        drive.userfs.settimes("source.txt", modified_time=datetime.today())

        drive.remotefs.setcontents("dest.txt", urandom(kb(2)))
        drive.remotefs.settimes("dest.txt", modified_time=datetime.today() - timedelta(days=1))
        # Act
        conflict = drive.has_conflict(src="source.txt", dst="dest.txt")
        # Assert
        assert not conflict

    def test_patchfile_ignores_update_if_size_is_same(self, drive):
        # Arrange
        new_data = urandom(kb(1))
        old_data = urandom(kb(1))

        drive.userfs.setcontents("source.txt", new_data)
        drive.remotefs.setcontents("source.txt", old_data)
        # Act
        drive.patchfile("source.txt")
        # Assert
        assert drive.remotefs.getcontents("source.txt") == old_data

    def test_patchfile_updates_remote(self, drive):
        # Arrange
        new_data = urandom(kb(2))
        old_data = urandom(kb(1))

        drive.userfs.setcontents("source.txt", new_data)
        drive.remotefs.setcontents("source.txt", old_data)
        # Act
        drive.patchfile("source.txt")
        # Assert
        assert drive.remotefs.getcontents("source.txt") == new_data


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
