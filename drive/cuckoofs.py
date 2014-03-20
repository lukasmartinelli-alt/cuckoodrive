# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from collections import defaultdict

from fs.filelike import FileLikeBase, FileWrapper
from fs.path import pathjoin
from fs.wrapfs.limitsizefs import LimitSizeFS


class AllocationSizeError(Exception):
    pass


class CuckooRemoteFS(LimitSizeFS):
    def __init__(self, fs, max_size):
        super(CuckooRemoteFS, self).__init__(fs, max_size)
        self._allocations = defaultdict(int)

    def free_space(self):
        """Calculate the space left of a filesystem. Already allocated space is also taken into account."""
        return self.max_size - self.cur_size - self.allocated_space

    @property
    def allocated_space(self):
        return sum(self._allocations.values())

    def allocate_space(self, space, path):
        if space > self.free_space():
            raise AllocationSizeError("""Cannot allocate {0}. Free space available
            on filesystem is {1}.""".format(self.allocation_size, self.free_space()))
        self._allocations[path] += space

    def deallocate_space(self, space, path):
        self._allocations[path] -= space


class CuckooFilePart(FileWrapper):
    def __init__(self, wrapped_file, mode, path):
        super(CuckooFilePart, self).__init__(wrapped_file, mode)



class CuckooFile(FileLikeBase):
    """
    A CuckooFile encapsulates many different smaller files that may reside on different other
    filesystems.
    """
    def __init__(self, path, mode, remote_filesystems, max_part_size):
        super(CuckooFile, self).__init__()
        self.path = path
        self.mode = mode
        self.remote_filesystems = remote_filesystems
        self.max_part_size = max_part_size
        self.parts = []
        self.current_part = None
        self.current_part_size = 0

    def best_fs(self):
        """Returns the filesystem that has the most free space."""
        return max(self.remote_filesystems, key=lambda fs: fs.free_space())

    def part_path(self):
        part_index = len(self.parts)
        return pathjoin(self.path, ".part{0}".format(part_index))

    def _read(self, sizehint=-1):


    def _write(self, data, flushing=False):
        """
        Write the given data to the underlying storages. The CuckooFile expands to a new
        file automatically if the max_part_size limit is reached with the current file pointer.
        """
        if not self.current_part:
            self.current_part = self.best_fs().open(path=self.part_path(), mode=self.mode)

        while self.current_part_size + len(data) > self.max_part_size:
            space_left = self.max_part_size - self.current_part_size
            self.current_part.write(data[0:space_left])
            self.current_part.close()

            self.current_part = self.best_fs().open(path=self.part_path(), mode=self.mode)
            self.current_part.write(data[space_left:])
            self.current_part_size += len(data[space_left:])

        self.current_part.write(data)
        self.current_part_size += len(data)