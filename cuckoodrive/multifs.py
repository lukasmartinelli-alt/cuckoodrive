# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.errors import (NoMetaError, ResourceNotFoundError, ResourceInvalidError,
                       RemoveRootError, NoSysPathError)
from fs.multifs import MultiFS
from fs.path import normpath


def free_space(fs):
    """
    Check whether the filesystem has information about how much space is left and return it.
    :param fs: filesystem to check for free space
    :return: Free space in Bytes
    :raise NoMetaError: If filesystem has no information about how much free space is left a
    NoMetaError exception is raised.
    """
    if hasattr(fs, "cur_size") and hasattr(fs, "max_size"):
        return fs.max_size - fs._get_cur_size()
    if fs.hasmeta("free_space"):
        return fs.getmeta("free_space")

    raise NoMetaError(meta_name="free_space", msg="FS has no meta information about free space")


class WritableMultiFS(MultiFS):
    """
    A filesystem that let's you write to the MultiFS without choosing a writefs explicitely.
    The WritableMultiFS chooses the best writefs automatically, by using the filesystem with the
    most space left
    """

    @property
    def writefs(self):
        """
        Access current writefs that should be used for writing
        :return: Writefs with the most free space left
        """
        writable_fs = [fs for fs in self.fs_sequence if not fs.closed]
        if len(writable_fs) > 0:
            return max(writable_fs, key=free_space)
        else:
            return None

    @writefs.setter
    def writefs(self, value):
        """You cannot change the writefs, because it is determined dynamically.
        :raise AttributeError:
        """
        if value is not None:
            raise AttributeError("Cannot set writefs with other value than None \
            as it is determined dynamically")

    def open(self, path, mode='r', buffering=-1, encoding=None, errors=None, newline=None,
             line_buffering=False, **kwargs):
        """Search the file and open it on the fileystem where it exists if read mode is specified.
        Otherwise the best writefs will be choosen and a file created.
        """
        if self.isdir(path):
            raise ResourceInvalidError(path)

        if 'r' in mode:
            for fs in self:
                if fs.exists(path):
                    return fs.open(path, mode=mode, buffering=buffering, encoding=encoding,
                                   errors=errors, newline=newline, line_buffering=line_buffering,
                                   **kwargs)

        if 'w' in mode and not '+' in mode and self.exists(path):
            self.remove(path)

        return super(WritableMultiFS, self).open(path, mode=mode, buffering=buffering,
                                                 encoding=encoding, errors=errors, newline=newline,
                                                 line_buffering=line_buffering, **kwargs)

    def remove(self, path):
        """Remove the file on all filesystems"""
        if self.isdir(path):
            raise ResourceInvalidError(path)

        affected_filesystems = [fs for fs in self if fs.exists(path)]

        if len(affected_filesystems) == 0:
            raise ResourceNotFoundError(path)

        for fs in affected_filesystems:
            fs.remove(path)

    def listdir(self, path="/", *args, **kwargs):
        """
        Default path has to be "/" and not "./" (like in the normal MultiFS implementation).
        Otherwise the absolute paths look really weird
        :raise ResourceNotFoundError: when given path does not exist
        """
        if not self.exists(path):
            raise ResourceNotFoundError(path)
        if not self.isdir(path):
            raise ResourceInvalidError(path)
        return super(WritableMultiFS, self).listdir(path, *args, **kwargs)

    def settimes(self, path, accessed_time=None, modified_time=None):
        """Set access and modify time on all filesystems that contain the the file"""
        affected_filesystems = [fs for fs in self if fs.exists(path)]
        for fs in affected_filesystems:
            fs.settimes(path, accessed_time, modified_time)

    def rename(self, src, dst):
        """Rename file on all filesystems where it exists"""
        affected_filesystems = [fs for fs in self if fs.exists(src)]
        for fs in affected_filesystems:
            fs.rename(src, dst)

    def removedir(self, path, recursive=False, force=False):
        if normpath(path) in ('', '/'):
            raise RemoveRootError(path)

        affected_filesystems = [fs for fs in self if fs.exists(path)]

        if len(affected_filesystems) == 0:
            raise ResourceNotFoundError(path)

        for fs in affected_filesystems:
            fs.removedir(path, recursive=recursive, force=force)

    def getsyspath(self, path, allow_none=False):
        """
        Because the file might be at severall different locations at the same time
        we cannot provide a unique syspath
        """
        if not allow_none:
            raise NoSysPathError(path=path)
        return None

    def makedir(self, path, **kwargs):
        for fs in self:
            fs.makedir(path, **kwargs)
