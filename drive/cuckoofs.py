# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.errors import FSError
from fs.filelike import FileLikeBase
from fs.path import pathjoin
from fs.wrapfs.limitsizefs import LimitSizeFS, LimitSizeFile


class CuckooRemoteFS(LimitSizeFS):
    """
    A CuckooRemoteFS has a max_size that cannot be overstepped. This functionality
    is provided by the underlying LimitSizeFS.
    """

    def __init__(self, fs, max_size):
        """Create a new CuckooRemoteFS from an existing filesystem
        :param fs: Filesystem to wrap around
        :param max_size: Max size that filesystem can grow to
        """
        super(CuckooRemoteFS, self).__init__(fs, max_size)

    def free_space(self):
        """Calculate the space left of a filesystem."""
        return self.max_size - self.cur_size


class CuckooFilePart(LimitSizeFile):
    """The CuckooFilePart is a part of a CuckooFile that has been splittet into multiple _parts,
    so that it can be distributed better and fulfills all file size restrictions of remote filesystems.
    A CuckooFilePart has a fixed max size. This functionality is implemented by the underlying
    LimitSizeFile.
    """

    def __init__(self, wrapped_file, mode, max_size, fs, path):
        """
        Create a new CuckooFilePart by wrapping it around an already existing wrapped_file.
        :param fs: Filesystem the wrapped_file the wrapped_file belongs to
        :param wrapped_file: Wrapped file that the CuckooFilePart extends
        :param mode: Mode the wrapped_file was opened with
        :param max_size: The maximum size the wrapped_file can reach
        :param path: Path of the wrapped_file (has to map to the real path of the wrapped_file part,
        not the virtual path of the CuckooFile)
        """
        super(CuckooFilePart, self).__init__(wrapped_file, mode, max_size, fs, path)


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
        self._parts = []
        self._fpointer = 0  # Current position of the file pointer
        self._expand()

    @property
    def best_fs(self):
        """Returns the filesystem that has the most free space."""
        return max(self.remote_filesystems, key=lambda fs: fs.free_space())

    def _fill(self, data):
        """File the current_part up with the given data and return the data
        that could not be written.
        :param data: The data to write to the current_part
        """
        space_left = self.max_part_size - (self._fpointer % self.max_part_size)
        self.current_part.write(data[0:space_left])
        self._fpointer += len(data[0:space_left])
        return data[space_left:]

    def _expand(self):
        """Expand the current_part to a new file. This will flush the old current_part and close the
        file handle."""
        self.current_part.close()
        new_part = self.best_fs.open(
            path=pathjoin(self.path, ".part{0}".format(len(self._parts))),
            mode=self.mode)
        self._parts.append(new_part)

    @property
    def current_part(self):
        """Calculates the current part by looking up in which part the file pointer must be"""
        size = 0
        for part in self._parts:
            size += part.size
            if size > self._fpointer:
                return part

        raise FSError("File pointer is no longer contained inside a part.")

    def _write(self, data, flushing=False):
        """
        Write the given data to the underlying storages. The CuckooFile expands to a new
        file automatically if _fpointer is getting bigger than the current_part
        """
        def current_part_to_small():
            return self._fpointer + len(data) > self.max_part_size

        if not current_part_to_small():
            self.current_part.write(data)
            self._fpointer += len(data)
        else:
            while current_part_to_small():
                data = self._fill(data)
                self._expand()
                self.current_part.write(data)
                self._fpointer += len(data)