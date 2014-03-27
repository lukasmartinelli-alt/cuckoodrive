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

    def listparts(self, path, full=False, absolute=False):
        """
        Return all parts for a given path.
        :param path: Path to check for parts
        :returns list of paths of parts
        """
        return self.wrapped_fs.listdir(path=dirname(path), wildcard="{0}.part*".format(basename(path)),
                                       full=full, absolute=absolute, files_only=True)

    @iotools.filelike_to_stream
    def open(self, path, mode='r', **kwargs):
        parts = [FilePart(open_part(part), mode, self.max_part_size) for part in self.listparts(path)]
                        
        return PartedFile(path, mode, self.wrapped_fs, self.max_part_size)

    def remove(self, path):
        """
        Remove a virtual file with path from the filesystem. This will delete all associated paths.
        """
        for part in self.listparts(path):
            self.wrapped_fs.remove(part)

    def listdir(self, path="", wildcard=None, full=False, absolute=False, dirs_only=False, files_only=False):
        """
        Lists the file and directories under a given path. This will return all .part0 files in the underlying fs
        as files and the other normal dirs as dirs.
        """
        print("LISTDIR")
        dirs = self.wrapped_fs.listdir(path=path, dirs_only=True, wildcard=wildcard, full=full, absolute=absolute)
        files = self.wrapped_fs.listdir(path=path, files_only=True, wildcard="*.part0", full=full, absolute=absolute)
        files = [splitext(f)[0] for f in files]
        if dirs_only:
            return dirs
        if files_only:
            return files
        return dirs + files

    def exists(self, path):
        """Check wether a path exists. Please use the virtual file names (without .part)"""
        return self.wrapped_fs.exists(path) or self.wrapped_fs.exists("{0}.part0".format(path))

    def isfile(self, path):
        return self.wrapped_fs.isfile("{0}.part0".format(path))


class PartSizeExceeded(Exception):
    pass


class FilePart(FileWrapper):
    """
    A part of a file (PartedFile) that can reach a maximum size and then must be extended to another part.
    """

    def __init__(self, wrapped_file, mode, max_size):
        """
        Create a new FilePart by wrapping it around an existing file.
        :param wrapped_file: The existing file to wrap around
        :param mode: The mode the wrapped_file was originally opened.
        :param max_size: The max size this part can reach.
        """
        super(FilePart, self).__init__(wrapped_file, mode)
        self.max_size = max_size
        self.size = 0
        self._file_pointer = 0

    def fill(self, data):
        """
        Fill the part up with the given data and return the data that could not be written.
        If all the data has been written it returns None.

        This might look similar to the standard IO convention, but we can't rely always on this implementation.

        :param data: The data to write to the part
        :return all data that could not be filled into this part or None if all data fit in
        """
        space_left = self.max_size - (self.tell() % self.max_size)
        if len(data) < space_left:
            self.write(data)  # TODO: It could be that the data cannot be all written, this case should be handled
            return None
        else:
            self.write(data[0:space_left])
            return data[space_left:]

    def _write(self, data, flushing=False):
        self._file_pointer += len(data)
        if self._file_pointer > self.size:
            self.size = self._file_pointer
        if self.size > self.max_size:
            raise PartSizeExceeded("Part cannot grow bigger than {0}.".format(self.max_size))

        self.wrapped_file.write(data)

    def _seek(self, offset, whence):
        self._file_pointer = offset
        self.wrapped_file.seek(offset, whence)


class InvalidFilePointerLocation(Exception):
    """
    An error that happens when the file pointer is in a negative offset or at a place where there
    is no part for it
    """
    pass


class PartedFile(FileLikeBase):
    """
    A PartedFile is composed out of many other smaller files (FilePart).
    """

    def __init__(self, path, mode, fs, max_part_size, parts=None):
        """
        Create a PartedFile for a path.
        :param parts: File handles to the associated parts
        :param path: Path of the virtual file
        :param mode: Mode with which the file was opened and with thich all the part_paths should be opened as well
        :param fs: Filesystem where this PartedFile exists
        :param max_part_size: The max a part of the file can reach
        """
        super(PartedFile, self).__init__()
        self.max_part_size = max_part_size

        self._path = path
        self._mode = mode
        self._fs = fs
        self._fpointer = 0  # Current position of the file pointer
        self._parts = parts if parts else []

    def _data_too_big(self, data):
        """Returns True if there is any data and it is longer than the left space in the file"""
        return data and self._fpointer + len(data) > self.max_part_size

    @property
    def current_part(self):
        """
        Calculates the current part by looking up in which part the file pointer must be.
        If there are no parts it returns None.

        If you've filled a part with all possible bytes and advances the _fpointer, the current_part
        will still be the part you've written to. To advance to the next part you should use _next_part or _expand
        """
        if len(self._parts) == 0:
            return None

        size = 0
        for part in self._parts:
            size += self.max_part_size
            if size >= self._fpointer:
                return part

        raise InvalidFilePointerLocation("File pointer points to a location that is not part of the file.")

    def _next_part(self):
        """Open and return the next part of the current_part"""
        next_index = self._parts.index(self.current_part) + 1
        if next_index < len(self._parts):
            next_part = self._parts[next_index]
            if next_part.closed:
                next_part.fs.open(next_part.path, next_part.mode)
            return next_part
        else:
            return None

    def _expand_part(self):
        """Expand the current_part to a new file and return it."""
        path = self._path + ".part{0}".format(len(self._parts))
        wrapped_part = self._fs.open(path, mode=self._mode)
        new_part = FilePart(wrapped_part, self._mode, self.max_part_size)
        self._parts.append(new_part)
        return new_part

    def _eof_reached(self):
        return self._fpointer == sum(part.size for part in self._parts)

    def _readall(self):
        all_data = bytes()
        for part in self._parts:
            part_data = part.read()
            self._fpointer += len(part_data)
            all_data += part_data
        return all_data

    def _readbuffered(self, sizehint):
        read_space = (self._fpointer % self.max_part_size)

        if read_space + sizehint > self.current_part.size:
            part_data = self.current_part.read(self.current_part.size - read_space)
            self._fpointer += len(part_data)

            next_part = self._next_part()

            if not next_part:
                return part_data

            next_part.seek(offset=0, whence=0)
            next_part_data = next_part.read(sizehint - len(part_data))
            self._fpointer += len(next_part_data)
            return part_data + next_part_data
        else:
            part_data = self.current_part.read(sizehint)
            self._fpointer += len(part_data)
            return part_data

    # --------------------------------------------------------------------
    # Essential Methods that are expected by the FileLikeBase
    # to be implemented and should behave as defined
    # --------------------------------------------------------------------
    def _read(self, sizehint=-1):
        if sizehint > self.max_part_size:
            raise NotImplementedError("Cannot read chunks bigger than a single part yet")
        if sizehint > 0:
            data = self._readbuffered(sizehint)
        else:
            data = self._readall()

        if len(data) > 0:
            return data
        else:
            return None

    def _write(self, data, flushing=False):
        def optional_flush(flushable):
            """Only flush if flushing has been set"""
            if flushing:
                flushable.flush()

        if not self.current_part:
            self._expand_part()

        if self._data_too_big(data):
            part = self.current_part
            while self._data_too_big(data):
                data = part.fill(data)
                optional_flush(part)
                if len(data) > 0:
                    part = self._expand_part()
            part.fill(data)
            optional_flush(part)
        else:
            self.current_part.write(data)
            self._fpointer += len(data)
            optional_flush(self.current_part)

    def _seek(self, offset, whence):
        if whence > 1:
            raise NotImplementedError("Only seeking to start is implemented yet.")

        for part in self._parts:
            part.seek(offset)

        self._fpointer = offset

    def _tell(self):
        return self._fpointer

    # --------------------------------------------------------------------
    # Altered behaviour of the FileLikeBase
    # --------------------------------------------------------------------
    def close(self):
        super(PartedFile, self).close()
        for part in self._parts:
            part.close()