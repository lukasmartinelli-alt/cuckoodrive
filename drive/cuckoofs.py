# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.filelike import FileLikeBase
from fs.wrapfs.limitsizefs import LimitSizeFS, LimitSizeFile


class CuckooFilePartMissingError(Exception):
    pass


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

    @property
    def best_fs(self):
        """Returns the filesystem that has the most free space."""
        return max(self.remote_filesystems, key=lambda fs: fs.free_space())

    def _fill(self, data, part):
        """File the given part up with the given data and return the data
        that could not be written. If all data has been written return None.
        :param data: The data to write to the current_part
        """
        space_left = self.max_part_size - (self._fpointer % self.max_part_size)
        if len(data) < space_left:
            part.write(data)
            return None
        else:
            part.write(data[0:space_left])
            self._fpointer += len(data[0:space_left])
            return data[space_left:]

    def _expand(self):
        """Expand the current_part to a new file and return it."""
        new_part = self.best_fs.open(
            path=self.path + ".part{0}".format(len(self._parts)),
            mode=self.mode)
        self._parts.append(new_part)
        return new_part

    @property
    def current_part(self):
        """Calculates the current part by looking up in which part the file pointer must be"""
        if len(self._parts) == 0:
            return None

        size = 0
        for part in self._parts:
            size += self.max_part_size
            if size >= self._fpointer:
                return part

        raise CuckooFilePartMissingError("File pointer points to bytes that are in no part.")

    def _write(self, data, flushing=False):
        """
        Write the given data to the underlying storages. The CuckooFile expands to a new
        file automatically if _fpointer is getting bigger than the current_part
        """
        def data_is_bigger_than_max_part_size():
            return data and self._fpointer + len(data) > self.max_part_size

        def optional_flush(flashable_part):
            if flushing:
                flashable_part.flush()

        if not self.current_part:
            self._expand()

        if not data_is_bigger_than_max_part_size():
            self.current_part.write(data)
            optional_flush(self.current_part)
            self._fpointer += len(data)
        else:
            part = self.current_part
            data = self._fill(data, part)
            optional_flush(part)
            while data_is_bigger_than_max_part_size():
                part = self._expand()
                data = self._fill(data, part)
                optional_flush(part)

    def _seek(self, offset, whence):
        if whence > 1:
            raise NotImplementedError("Only seeking to start is implemented yet.")

        for part in self._parts:
            part.seek(offset)

        self._fpointer = offset

    def close(self):
        for part in self._parts:
            part.close()
        super(CuckooFile, self).close()