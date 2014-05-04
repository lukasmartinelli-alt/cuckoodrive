# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.expose import fuse
from fs.opener import fsopendir
from fs.wrapfs.debugfs import DebugFS
from fs.osfs import OSFS
from fs.utils import copyfile, copydir

from cuckoodrive.multifs import WritableMultiFS
from cuckoodrive.partedfs import PartedFS
from cuckoodrive.utils import mb


class CuckooDrive(object):
    """Represents a cuckoo drive either in mounted or in synchronized mode."""
    skip_methods = ('listdir', 'listdirinfo', 'getinfo', 'exists', 'isfile', 'getsize')
    file_size = mb(10)

    def __init__(self, path, remotes, verbose=False):
        self.path = path
        self.verbose = verbose
        self.remotefs = self._remotefs(remotes)

    def _remotefs(self, remotes):
        """Create a MultiFS of all the remote filesystems"""
        def verbose_fs(wrapped_fs, identifier):
            if self.verbose:
                return DebugFS(wrapped_fs, identifier=identifier,
                               skip=self.skip_methods, verbose=False)
            return wrapped_fs

        multifs = verbose_fs(WritableMultiFS(), "MultiFS")

        for fs_uri in remotes:
            print(fs_uri)
            remote_fs = verbose_fs(fsopendir(fs_uri), "Remote@{0}".format(fs_uri))
            multifs.addfs(fs_uri, remote_fs)

        partedfs = verbose_fs(PartedFS(multifs, self.file_size), "PartedFS")
        return partedfs


class MountedCuckooDrive(CuckooDrive):
    def __init__(self, path, remotes, **kwargs):
        super(MountedCuckooDrive, self).__init__(path, remotes, **kwargs)
        self.mount()

    def mount(self):
        """
        Mount the remote filesystems as a FUSE or Dokan filesystem.
        This allows you to use cuckoo drive exactly for your purposes.
        """
        try:
            mp = fuse.mount(self.remotefs, self.path)
            print("Mounted cuckoo drive at " + mp.path)
            print("Press any key to unmount")
            raw_input()
            print("Unmounting cuckoo drive")
            mp.unmount()
        except RuntimeError:
            print("Failed mounting cuckoo drive")
            raise


class SyncedCuckooDrive(CuckooDrive):
    def __init__(self, path, remotes, **kwargs):
        super(SyncedCuckooDrive, self).__init__(path, remotes, **kwargs)
        self.fs = OSFS(path)
        self.sync_dirs()
        self.sync_files()

    def sync_dirs(self):
        for path in self.fs.walkdirs():
            if not self.remotefs.exists(path):
                copydir((self.fs, path), (self.remotefs, path))

    def sync_files(self):
        for path in self.fs.walkfiles():
            if self.remotefs.exists(path):
                self.remotefs
            else:
                copyfile(self.fs, path, self.remotefs, path)
