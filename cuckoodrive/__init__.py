# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.expose import fuse
from fs.opener import fsopendir
from fs.wrapfs.debugfs import DebugFS
from fs.osfs import OSFS
from fs.utils import copyfile, copydir
from fs.wrapfs import WrapFS

from cuckoodrive.multifs import WritableMultiFS
from cuckoodrive.partedfs import PartedFS
from cuckoodrive.utils import mb


class CuckooDriveFS(WrapFS):
    skip_methods = ('listdir', 'listdirinfo', 'getinfo', 'exists', 'isfile', 'getsize')
    file_size = mb(10)

    def __init__(self, remote_filesystems, verbose=False):
        self.verbose = verbose
        fs = self._create_fs(remote_filesystems)
        super(CuckooDriveFS, self).__init__(fs)

    def _create_fs(self, remote_filesystems):
        """Create the cuckoo drive fileystem out of the remote filesystems"""
        multifs = CuckooDriveFS.verbose_fs(WritableMultiFS(), "MultiFS", self.verbose)
        for idx, remote_fs in enumerate(remote_filesystems):
            multifs.addfs("Remote{0}".format(idx), remote_fs)

        return CuckooDriveFS.verbose_fs(PartedFS(multifs, self.file_size),
                                        "PartedFS",
                                        self.verbose)

    @staticmethod
    def verbose_fs(wrapped_fs, identifier, verbose):
        """Wrap the filesystem into a DebugFS if the verbose option is specified"""
        if verbose:
            return DebugFS(wrapped_fs, identifier=identifier,
                           skip=CuckooDriveFS.skip_methods, verbose=False)
        return wrapped_fs

    @classmethod
    def from_uris(cls, remote_uris, verbose):
        """Create remote filesystem for each given uri and return them"""
        def create_fs(idx, fs_uri):
            return CuckooDriveFS.verbose_fs(fsopendir(fs_uri), "Remote{0}".format(idx), verbose)

        remote_filesystems = [create_fs(idx, fs_uri) for idx, fs_uri in enumerate(remote_uris)]
        return cls(remote_filesystems, verbose)


class CuckooDrive(object):
    """Represents a cuckoo drive either in mounted or in synchronized mode."""
    def __init__(self, path, remote_uris, verbose=False):
        self.path = path
        self.remotefs = CuckooDriveFS.from_uris(remote_uris, verbose=verbose)


class MountedCuckooDrive(CuckooDrive):
    def __init__(self, path, remote_uris, **kwargs):
        super(MountedCuckooDrive, self).__init__(path, remote_uris, **kwargs)

    def mount(self):
        """
        Mount the remote filesystems as a FUSE or Dokan filesystem.
        This allows you to use cuckoo drive exactly for your purposes.
        """
        try:
            self.mp = fuse.mount(self.remotefs, self.path)
        except RuntimeError:
            print("Failed mounting cuckoo drive")
            raise

    def unmount(self):
        try:
            self.mp.unmount()
        except RuntimeError:
            print("Failed unmounting cuckoo drive")
            raise


class SyncedCuckooDrive(CuckooDrive):
    def __init__(self, path, remote_uris, **kwargs):
        super(SyncedCuckooDrive, self).__init__(path, remote_uris, **kwargs)
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
