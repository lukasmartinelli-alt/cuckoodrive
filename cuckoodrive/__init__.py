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

    def __init__(self, path, remote_filesystems, verbose=False):
        self.path = path
        self.verbose = verbose
        self.remotefs = self._create_fs(remote_filesystems)

    @staticmethod
    def create_remote_filesystems_from_uris(remote_uris, verbose):
        """Create remote filesystem for each given uri and return them"""
        for idx, fs_uri in enumerate(remote_uris):
            yield CuckooDrive.verbose_fs(fsopendir(fs_uri), "Remote{0}".format(idx), verbose)

    @staticmethod
    def verbose_fs(wrapped_fs, identifier, verbose):
        """Wrap the filesystem into a DebugFS if the verbose option is specified"""
        if verbose:
            return DebugFS(wrapped_fs, identifier=identifier,
                           skip=CuckooDrive.skip_methods, verbose=False)
        return wrapped_fs

    def _create_fs(self, remote_filesystems):
        """Create the cuckoo drive fileystem out of the remote filesystems"""
        multifs = CuckooDrive.verbose_fs(WritableMultiFS(), "MultiFS", self.verbose)
        for idx, remote_fs in enumerate(remote_filesystems):
            multifs.addfs("Remote{0}".format(idx), remote_fs)

        return CuckooDrive.verbose_fs(PartedFS(multifs, self.file_size), "PartedFS", self.verbose)


class MountedCuckooDrive(CuckooDrive):
    def __init__(self, path, remotes, verbose=False):
        remote_filesystems = CuckooDrive.create_remote_filesystems_from_uris(remotes, verbose)
        super(MountedCuckooDrive, self).__init__(path, remote_filesystems, verbose)
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
    def __init__(self, path, remotes, verbose=False):
        remote_filesystems = CuckooDrive.create_remote_filesystems_from_uris(remotes, verbose)
        super(SyncedCuckooDrive, self).__init__(path, remote_filesystems, verbose)
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
