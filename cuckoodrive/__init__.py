# -*- coding: utf-8 -*-
"""
CuckooDrive emulates a user filesystem that aggregates all the free space provided on various
cloud storage providers into one big drive.

Usage:
  cuckoodrive sync [--watch] [-v | --verbose] --remotes <fs_uri>...
  cuckoodrive (-h | --help)
  cuckoodrive --version

Options:
  -h --help     Show this screen.
  --remotes     Filesystem URIs of remote filesystems
  --version     Show version
  --watch       Watch path for changes and synchronize them automatically
  -v --verbose  Print all filesystem actions to stdout

Example #1:
  cuckoodrive sync --remotes dropbox://morgenkaffee  googledrive://morgenkaffe
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import os
import signal
import sys

from docopt import docopt
from blessings import Terminal

from fs.opener import fsopendir
from fs.wrapfs.debugfs import DebugFS
from fs.osfs import OSFS
from fs.utils import copyfile, copydir
from fs.wrapfs import WrapFS
from fs.watch import ensure_watchable
import fs.watch

from cuckoodrive.multifs import WritableMultiFS
from cuckoodrive.partedfs import PartedFS
from cuckoodrive.utils import mb
from cuckoodrive.filelock import FileLock

term = Terminal()


class CuckooDriveFS(WrapFS):
    """This filesystem is used in CuckooDrive an basically encapsulates a PartedFS on top of
    a WritableMultiFS containg the custom cloud provider filesystems.

    The Filesystem stack usually looks something like this:

    +------------+------------+-----------+
    |               PartedFS              |
    +------------+------------+-----------+
    |            WritableMultiFS          |
    +------------+------------+-----------+
    | DropboxFS  | OneDriveFS | RemoteFS  |
    +------------+------------+-----------+

    You can aggregate every custom PyFilesystem you want. For testing we often use OSFS instances::
        fs = CuckooDriveFS(remote_filesystems=[OSFS('/tmp/fs1'), OSFS('/tmp/fs2')])

    You can also use the filesystem URI syntax to create a CuckooDriveFS::
        fs = CuckooDriveFS.from_uris(remote_uris=['/tmp/fs1', '/tmp/fs1'])

    This works for all filesystem that have an Opener implemented::
        fs = CuckooDriveFS.from_uris(remote_uris=['dropbox://morgenkaffee/cuckoo'])

    When the verbose option is specified, each filesystem is wrapped in a DebugFS that logs
    every action.

    Manipulate the maximum file_size of a PartFile of the PartedFS::
        CuckooDriveFS.file_size = mb(40)
    """
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
    def from_uris(cls, remote_uris, verbose=False):
        """Create remote filesystem for each given uri and return them"""
        def create_fs(idx, fs_uri):
            return CuckooDriveFS.verbose_fs(fsopendir(fs_uri), "Remote{0}".format(idx), verbose)

        remote_filesystems = [create_fs(idx, fs_uri) for idx, fs_uri in enumerate(remote_uris)]
        return cls(remote_filesystems, verbose)


class SyncedCuckooDrive(object):
    """
    Watches and synchronizes a local path with the remote_fs.
    The underlying CuckooDriveFS is initialized from the passed remote_uris.
    """
    def __init__(self, path, remote_uris, watch=False, verbose=False):
        self.path = path
        self.remotefs = CuckooDriveFS.from_uris(remote_uris, verbose=verbose)
        self.userfs = OSFS(path)

        if watch:
            ensure_watchable(self.userfs)
            self.userfs.add_watcher(self.userfs_changed)

        with FileLock(self.remotefs):
            self.sync_dirs()
            self.sync_files()

    def userfs_changed(self, event):
        ignored_events = (fs.watch.ACCESSED, fs.watch.CLOSED)
        if type(event) not in ignored_events:
            event_name = event.__class__.__name__.lower()
            message = 4 * " " + event_name + " " + term.normal + event.path

            if type(event) is fs.watch.CREATED:
                print(term.green + message)
            elif type(event) is fs.watch.MODIFIED:
                print(term.yellow + message)
            elif type(event) is fs.watch.REMOVED:
                print(term.red + message)
            elif type(event) in (fs.watch.MOVED_DST, fs.watch.MOVED_SRC):
                print(term.cyan + message)
            else:
                print(message)
            # Handle specific events
            # for now just resynchronize
            self.sync_dirs()
            self.sync_files()

    def sync_dirs(self):
        for path in self.userfs.walkdirs():
            if not self.remotefs.exists(path):
                copydir((self.userfs, path), (self.remotefs, path))

    def sync_files(self):
        for path in self.userfs.walkfiles():
            if self.remotefs.exists(path):
                self.remotefs
            else:
                copyfile(self.userfs, path, self.remotefs, path)


def main():
    arguments = docopt(__doc__, version="CuckooDrive 0.0.1")
    path = os.getcwd()
    watch = arguments["--watch"]
    verbose = arguments["--verbose"]
    remotes = arguments["<fs_uri>"]

    def sync_aborted(signal, frame):
        print('Stopped synchronizing!')
        sys.exit(0)

    def wait_abort():
        while True:
            continue

    if arguments["sync"]:
        signal.signal(signal.SIGINT, sync_aborted)
        SyncedCuckooDrive(path, remotes, watch=watch, verbose=verbose)
        if watch:
            print(">>> CuckooDrive is watching for changes. Press Ctrl-C to Stop.")
            wait_abort()
