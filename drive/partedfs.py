# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
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

    def _encode(self, path):
        """
        Add the .part0 extension to the given path
        :param path: The plain path to encode
        :returns Encoded path (without .part extension)
        """
        return "{0}.part0".format(path)

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


class PartSizeExceeded(Exception):
    pass


class FilePart(object):
    pass