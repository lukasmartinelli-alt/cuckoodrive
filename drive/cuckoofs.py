# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from collections import defaultdict
from fs.errors import FSError

from fs.filelike import FileLikeBase, FileWrapper
from fs.path import pathjoin
from fs.wrapfs.limitsizefs import LimitSizeFS, LimitSizeFile


class AllocationSizeError(Exception):
    pass


class CuckooRemoteFS(LimitSizeFS):
    """
    A wrapper around remote filesystems that implements useful mechanisms
    for dealing with the process of dynamically allocating new files.
    A CuckooRemoteFS has a max_size that cannot be overstepped. This functionality
    is provided by the underlying LimitSizeFS.
    The CuckooRemoteFS keeps tracks of made allocations.
    """

    def __init__(self, fs, max_size):
        """Create a new CuckooRemoteFS from an existing filesystem
        :param fs: Filesystem to wrap around
        :param max_size: Max size that filesystem can grow to
        """
        super(CuckooRemoteFS, self).__init__(fs, max_size)
        self._allocations = defaultdict(int)  # A list of allocations made

    def free_space(self):
        """Calculate the space left of a filesystem. Already allocated space is also taken into account."""
        return self.max_size - self.cur_size - self.allocated_space

    @property
    def allocated_space(self):
        """Return the total allcoated space"""
        return sum(self._allocations.values())

    def allocate_space(self, space, path):
        """Allocate space for a certain path. After the file has been written the space has to be
        deallocated by deallocate_space.
        :param space: Space in Bytes to allocate
        :param path: Path to allocate for
        """
        if space > self.free_space():
            raise AllocationSizeError("""Cannot allocate {0}. Free space available
            on filesystem is {1}.""".format(self.allocation_size, self.free_space()))
        self._allocations[path] += space

    def deallocate_space(self, space, path):
        """Remove the previously made allocations.
        :param space: Amount of space to deallocate
        :param path: Path to deallocatee for
        """
        self._allocations[path] -= space


class CuckooFilePart(LimitSizeFile):
    """The CuckooFilePart is a part of a CuckooFile that has been splittet into multiple parts,
    so that it can be distributed better and fulfills all file size restrictions of remote filesystems.
    A CuckooFilePart has a fixed max size. This functionality is implemented by the underlying
    LimitSizeFile.
    """

    def __init__(self, file, mode, max_size, path):
        """
        Create a new CuckooFilePart by wrapping it around an already existing file.
        :param file: Wrapped file
        :param mode: Mode the file was opened with
        :param max_size: The maximum size the file can reach
        :param path: Path of the file (has to map to the real path of the file part, not the owner file)
        """
        super(CuckooFilePart, self).__init__(file, mode, max_size, fs, path)


class CuckooFile(FileLikeBase):
    """
    A CuckooFile encapsulates many smaller files (CuckooPartFile) that reside on remote filesystems.
    A CuckooFile is only a virtual construct, the real data is in the underlying parts.
    """

    def __init__(self, path, mode, remote_filesystems, max_part_size=8 * 1024 * 1024):
        """Create a new cuckoo file.
        :param path: Virtual path of the file. The real paths are consinsting of the paths of the parts.
        :param mode: Mode the file was opened with
        :param remote_filesystems: Remote filesystems the CuckooFilePart's are distributed on.
        :param max_part_size: Maximum size for a single CuckooPartFile
        """
        super(CuckooFile, self).__init__()
        self.path = path
        self.mode = mode
        self.remote_filesystems = remote_filesystems
        self.max_part_size = max_part_size

        # Fields for file functionality
        self.parts = []
        self.file_pointer = 0

        self._expand_new_part()

    @property
    def best_fs(self):
        """Returns the filesystem that has the most free space."""
        return max(self.remote_filesystems, key=lambda fs: fs.free_space())

    def _expand_new_part(self):
        part_path = pathjoin(self.path, ".part{0}".format(len(self.parts)))
        new_part = self.best_fs.open(part_path, mode=self.mode)
        self.parts.append(new_part)

    @property
    def current_part(self):
        """Calculates the current part by looking up in which part the file pointer must be"""
        size = 0
        for part in self.parts:
            size += part.size
            if size > self.file_pointer:
                return part

        raise FSError("File pointer is no longer contained inside a part.")

    def _read(self, sizehint=-1):
        pass

    def _write(self, data, flushing=False):
        """
        Write the given data to the underlying storages. The CuckooFile expands to a new
        file automatically if file_pointer is getting bigger than the current_part
        """
        while self.file_pointer + len(data) > self.max_part_size:
            space_left = self.max_part_size - self.file_pointer
            self.current_part.write(data[0:space_left])
            self.file_pointer += len(data[0:space_left])
            self._expand_new_part()
            self.current_part.write(data[space_left:])
            self.file_pointer += len(data[space_left:])

        self.current_part.write(data)
        self.file_pointer += len(data)