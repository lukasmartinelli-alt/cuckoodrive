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
import json

from docopt import docopt
from blessings import Terminal

from fs.opener import opener, fsopendir
from fs.wrapfs.debugfs import DebugFS
from fs.osfs import OSFS
from fs.utils import copyfile, copydir
from fs.wrapfs import WrapFS
from fs.watch import ensure_watchable
from fs.appdirfs import UserDataFS
import fs.watch

from dropboxfs import DropboxOpener

from cuckoodrive.multifs import WritableMultiFS
from cuckoodrive.partedfs import PartedFS
from cuckoodrive.utils import mb
from cuckoodrive.filelock import FileLock

term = Terminal()
settings_fs = UserDataFS("cuckoodrive", appauthor="Lukas Martinelli")


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
    def __init__(self, userfs, remotefs, mode="update", watch=False, verbose=False):
        self.userfs = userfs
        self.remotefs = remotefs
        self.mode = mode

        if watch:
            ensure_watchable(self.userfs)
            self.userfs.add_watcher(self.userfs_changed)

        with FileLock(self.remotefs):
            self.sync_dirs()
            self.sync_files()

    @staticmethod
    def create_event_message(event):
        event_name = event.__class__.__name__.lower()
        message = 4 * " " + event_name + " " + term.normal + event.path

        if type(event) is fs.watch.CREATED:
            return term.green + message
        elif type(event) is fs.watch.MODIFIED:
            return term.yellow + message
        elif type(event) is fs.watch.REMOVED:
            return term.red + message
        elif type(event) in (fs.watch.MOVED_DST, fs.watch.MOVED_SRC):
            return term.cyan + message
        else:
            return message

    def userfs_changed(self, event):
        ignored_events = (fs.watch.ACCESSED, fs.watch.CLOSED)
        if type(event) not in ignored_events:
            message = self.create_event_message(event)
            print(message)
            self.sync_dirs()
            self.sync_files()

    def sync_dirs(self):
        for path in self.userfs.walkdirs():
            if not self.remotefs.exists(path):
                copydir((self.userfs, path), (self.remotefs, path))
                print(term.green + " " * 4 + "copied " + path + term.normal)

    def has_conflict(self, src, dst):
        src_info = self.userfs.getinfo(src)
        dst_info = self.remotefs.getinfo(dst)
        return src_info["modified_time"] < dst_info["modified_time"]

    def patchfile(self, path):
        """Patch remote file with new user file if size has changed"""
        user_info = self.userfs.getinfo(path)
        remote_info = self.remotefs.getinfo(path)

        if user_info["size"] != remote_info["size"]:
            copyfile(self.userfs, path, self.remotefs, path, overwrite=True)
            print(term.yellow + " " * 4 + "updated " + path + term.normal)

    def sync_files(self):
        """Copy files that don't exist on remote fs or patch them if they do exist"""
        if self.mode != "update":
            raise NotImplementedError("Only the update mode has been implemented yet.")

        for path in self.userfs.walkfiles():
            if self.remotefs.exists(path):
                self.patchfile(path)
            else:
                copyfile(self.userfs, path, self.remotefs, path, overwrite=False)
                print(term.green + " " * 4 + "copied " + path + term.normal)


class CuckooDropboxOpener(DropboxOpener):
    @staticmethod
    def get_options(username):
        options = {
            "app_key":"bhhdl31c1xlca9g",
            "app_secret":"kt8q37wti4i8by7",
            "app_type":"app_folder"
        }
        file_name = "{0}_dropbox.json".format(username)

        if not settings_fs.exists(file_name):
            with settings_fs.open(file_name, mode="wb") as fh:
                json.dump(options, fh, indent=4, sort_keys=True)
        else:
            with settings_fs.open(file_name, mode="rb") as fh:
                options = json.load(fh)

        return options

    @staticmethod
    def update_options(username, options):
        with settings_fs.open("{0}_dropbox.json".format(username), mode="wb") as fh:
            json.dump(options, fh, indent=4, sort_keys=True)

def main():
    arguments = docopt(__doc__, version="CuckooDrive 0.0.1")
    path = os.getcwd()
    watch = arguments["--watch"]
    verbose = arguments["--verbose"]
    remote_uris = arguments["<fs_uri>"]

    def register_openers():
        opener.add(CuckooDropboxOpener)

    def sync_aborted(signal, frame):
        print('Stopped synchronizing!')
        sys.exit(0)

    def wait_abort():
        while True:
            continue

    register_openers()
    remotefs = CuckooDriveFS.from_uris(remote_uris, verbose=verbose)
    userfs = OSFS(path)

    if arguments["sync"]:
        signal.signal(signal.SIGINT, sync_aborted)
        print(">>> CuckooDrive is synchronizing {0}".format(path))
        SyncedCuckooDrive(userfs, remotefs, watch=watch, verbose=verbose)
        if watch:
            print(">>> CuckooDrive is watching for changes. Press Ctrl-C to Stop.")
            wait_abort()
