# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
import stat
from fs import iotools
from fs.errors import ResourceNotFoundError, ResourceInvalidError
from fs.filelike import FileLikeBase, FileWrapper
from fs.path import dirname, basename, splitext
from fs.wrapfs import WrapFS, wrap_fs_methods


class PartedFS(WrapFS):
    """
    A virtual filesystem that splits large files into many smaller files.
    This filesystem uses an underlying filesystem to translate the many small files back and forth.

    The process actually takes a large file and splits it into parts with a max size.
    So a file like 'backup.tar' in the folder '/backups' with 240 MB will translate into following files::

    `-- backups
        |-- backup.tar.part0 (100MB)
        |-- backup.tar.part1 (100MB)
        `-- backup.tar.part2 (40MB)

    If the max part size would have been set to 300 MB, there will only be a single file, but for simplicity sake,
    still managed as a part (so we can easily extend the file later)::

    `-- backups
        `-- backup.tar.part0 (240MB)

    One problem is, that we never know wether a file is complete, because there might
    be one missing part.
    """

    _meta = {
        "virtual": True,
        "read_only": False,
        "unicode_paths": True,
        "case_insensitive_paths": False
    }

    def __init__(self, fs, max_part_size):
        """
        Create a PartedFS with an underlying filesystem.
        :param fs: The underlying filesystem where the many small files will be stored
        :param max_part_size: The max size one part of a file can reach.
        """
        self.max_part_size = max_part_size
        super(PartedFS, self).__init__(fs)

    def _encode(self, path, part_index=0):
        """
        Add the .part0 extension to the given path
        :param path: The plain path to encode
        :returns Encoded path (without .part extension)
        """
        return "{0}.part{1}".format(path, part_index)

    def _decode(self, path):
        """
        Remove the .part[0-9] extension from the given path
        :param path: Encoded path
        :returns Decoded path (added .part extension)
        """
        return splitext(path)[0]

    def listparts(self, path, full=False, absolute=False):
        """
        Return all parts for a given path.
        :param path: Path to check for parts
        :returns list of paths of parts
        """
        return self.wrapped_fs.listdir(path=dirname(path), wildcard="{0}.part*".format(basename(path)),
                                       full=full, absolute=absolute, files_only=True)

    def remove(self, path):
        """
        Remove a virtual file with path from the filesystem. This will delete all associated paths.
        :param path: Raw path of where to remove all the associated paths
        """
        for part in self.listparts(path):
            self.wrapped_fs.remove(part)

    def listdir(self, path="", wildcard=None, full=False, absolute=False, dirs_only=False, files_only=False):
        """
        Lists the file and directories under a given path. This will return all .part0 files in the underlying fs
        as files and the other normal dirs as dirs.
        """
        dirs = self.wrapped_fs.listdir(path=path, dirs_only=True, wildcard=wildcard, full=full, absolute=absolute)
        files = self.wrapped_fs.listdir(path=path, files_only=True, wildcard="*.part0", full=full, absolute=absolute)
        files = [self._decode(f) for f in files]
        if dirs_only:
            return dirs
        if files_only:
            return files
        return dirs + files

    def exists(self, path):
        """
        Check wether the encoded path exists on the wrapped_fs. If the normal path exists as well
        it is a directory and should also return True
        :param path: Path that will be encoded and checked wether it exists
        """
        return self.wrapped_fs.exists(path) or self.wrapped_fs.exists(self._encode(path))

    def isfile(self, path):
        """
        Check wether the encoded path is a file on the wrapped_fs
        """
        return self.wrapped_fs.isfile(self._encode(path))

    def open(self, path, mode='r', **kwargs):
        """
        Open a new PartedFile. We will always set at least the file for part0.
        """

        def create_file_part(part_path):
            f = self.wrapped_fs.open(part_path, mode, **kwargs)
            return FilePart(f)

        if self.isdir(path):
            raise ResourceInvalidError(path)

        if "w" not in mode and "a" not in mode:
            if self.exists(path):
                parts = [create_file_part(p) for p in self.listparts(path)]
                return PartedFile(fs=self.wrapped_fs, path=path, mode=mode,
                                  max_part_size=self.max_part_size, parts=parts)
            else:
                raise ResourceNotFoundError(path)
        if "w" in mode and self.exists(path):
            self.remove(path)

        return PartedFile(fs=self.wrapped_fs, path=path, mode=mode,
                          max_part_size=self.max_part_size, parts=[create_file_part(self._encode(path))])

    def rename(self, src, dst):
        """
        Rename all parts accordingly.
        """
        if not self.exists(src):
            raise ResourceNotFoundError(src)
        for idx, part in enumerate(sorted(self.listparts(src))):
            part_src = self._encode(self._decode(part), part_index=idx)
            part_dst = self._encode(dst, part_index=idx)
            self.wrapped_fs.rename(part_src, part_dst)

    def getinfo(self, path):
        """
        Assemble the info of all the parts and use the most recent updated
        timestamps of the parts as values of the file.
        """
        if not self.exists(path):
            raise ResourceNotFoundError(path)

        part_infos = [self.wrapped_fs.getinfo(part) for part in self.listparts(path)]
        info = {
            "parts": part_infos,
            "size": self.getsize(path),
            "created_time": max([i["modified_time"] for i in part_infos]),
            "modified_time": max([i["modified_time"] for i in part_infos]),
            "accessed_time": max([i["accessed_time"] for i in part_infos])
        }

        return info

    def copy(self, src, dst, **kwds):
        """
        Copies a file from src to dst. This will copy al the parts of one file
        to the respective location of the new file
        """
        if not self.exists(src):
            raise ResourceNotFoundError(src)
        for idx, part_src in enumerate(sorted(self.listparts(src))):
            part_dst = self._encode(dst, idx)
            self.wrapped_fs.copy(part_src, part_dst, **kwds)

    def getsize(self, path):
        """
        Calculates the sum of all parts as filesize
        """
        if not self.exists(path):
            raise ResourceNotFoundError(path)
        return sum([self.wrapped_fs.getsize(part) for part in self.listparts(path)])


class PartSizeExceeded(Exception):
    pass


class InvalidFilePointerLocation(Exception):
    pass


class PartedFile(FileLikeBase):
    """
    A PartedFile is composed out of many other smaller files (FilePart).
    A PartedFile has a current_part attribute, where the current part is calculated based on the
    internal file pointer.
    The FileLikeBase implements alot of functionality that allows us to keep this class lightweight.
    The _write method for example, just tries to write the data, that can fit into the current part,
    the rest is returned. The FileLikeBase will buffer that by itself and look that this will be written again.
    """

    def __init__(self, fs, path, mode, parts, max_part_size):
        super(PartedFile, self).__init__()
        self._path = path
        self._fs = fs
        self._file_pointer = 0
        self._mode = mode

        self.parts = parts
        self.max_part_size = max_part_size

    @property
    def current_part(self):
        """
        Calculates the current part by looking up in which part the file pointer must be.
        If there are no parts it returns None.
        """
        size = 0
        for part in self.parts:
            size += self.max_part_size
            if size > self._file_pointer:
                return part

        if self._mode == "r":
            raise InvalidFilePointerLocation("File pointer points to a location that is not part of the file.")
        else:
            return self._expand_part()

    def _expand_part(self):
        """
        Expand the current_part to a new file and return it.
        TODO: this logic should perhaps go into the filesystem not the file
        """
        path = self._path + ".part{0}".format(len(self.parts))
        wrapped_part = self._fs.open(path, mode=self._mode)
        new_part = FilePart(wrapped_part)
        self.parts.append(new_part)
        return new_part

    @property
    def _space_left(self):
        return self.max_part_size - (self._file_pointer % self.max_part_size)

    def _write(self, data, flushing=False):
        if data and len(data) > self._space_left:
            self.current_part.write(data[:self._space_left])
            unwritten_data = data[self._space_left:]
            self._file_pointer += len(data) - len(unwritten_data)
            return unwritten_data if not flushing else self._write(unwritten_data, flushing)
        else:
            self.current_part.write(data)
            self._file_pointer += len(data)


class FilePart(FileWrapper):
    """
    A part of a file (PartedFile) that can reach a maximum size and then must be extended to another part.
    """

    def __init__(self, wrapped_file):
        super(FilePart, self).__init__(wrapped_file)