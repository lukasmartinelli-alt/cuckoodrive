# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from fs.errors import NoMetaError

from fs.multifs import MultiFS


def free_space(fs):
    if fs.hasmeta("free_space"):
        return fs.getmeta("free_space")
    if hasattr(fs, "cur_size") and hasattr(fs, "max_size"):
        return fs.max_size - fs.cur_size
    raise NoMetaError(meta_name="free_space", msg="FS has no meta information about free space")


class WritableMultiFS(MultiFS):
    @property
    def writefs(self):
        writable_fs = [fs for fs in self.fs_sequence if not fs.closed]
        if len(writable_fs) > 0:
            return max(writable_fs, key=free_space)
        else:
            return None

    @writefs.setter
    def writefs(self, value):
        if value is not None:
            raise AttributeError("Cannot set writefs with other value than None as it is determined dynamically")