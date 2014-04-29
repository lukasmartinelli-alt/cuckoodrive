# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from fs.errors import NoMetaError

from fs.multifs import MultiFS


def free_space(fs):
    """
    Check whether the filesystem has information about how much space is left and return it.
    :param fs: filesystem to check for free space
    :return: Free space in Bytes
    :raise NoMetaError: If filesystem has no information about how much free space is left a
    NoMetaError exception is raised.
    """
    if fs.hasmeta("free_space"):
        return fs.getmeta("free_space")
    if hasattr(fs, "cur_size") and hasattr(fs, "max_size"):
        return fs.max_size - fs.cur_size
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