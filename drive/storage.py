from __future__ import print_function, division, absolute_import, unicode_literals


class Storage:
    """A Storage encapsulates a remote filesystem"""

    def __init__(self, name, fs, max_filesize=50 * 1024 * 1024):
        """
        Create a new storage with an underlying remote filesystem
        :param max_filesize: Max allowed upload file size
        :param fs: Underlying filesystem of the Storage
        :param name: Name of the Storage
        """
        self.max_filesize = max_filesize
        self.fs = fs
        self.name = name
        self.allocated_space = 0

    @property
    def free_space(self):
        """Calculate the space left of a storage. Already allocated space is also taken into account."""
        return self.fs.max_size - self.fs.cur_size - self.allocated_space

    def biggest_file(self):
        """Calculate the biggest possible file that is possible at the moment. The cap for the biggest
        file is not only the max_filesize but also the free_space"""
        if self.free_space <= 0:
            raise StorageSizeError("There is not enough space left for a file.")

        return self.free_space if self.max_filesize > self.free_space else self.max_filesize


class StorageSizeError(Exception):
    """Exception that is raised if a storage  or several storages have no more space left, even though
    more space is required"""
    pass


class StorageAllocation:
    """Information given by the StorageAllocator about what to write where"""

    def __init__(self, byte_range, storage):
        """
            Create an allocation that determines which bytes to write where
            :type byte_range: tuple
            :param byte_range: Which bytes to write (tuple containg the start byte and end byte)
            :param storage: Where to write the bytes
            """
        self.byte_range = byte_range
        self.storage = storage

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.byte_range == other.byte_range
                and self.storage == other.storage)

    def __repr__(self):
        return "<StorageAllocation: ({0},{1})@{2}>".format(self.byte_range[0], self.byte_range[1], self.storage.name)

    @property
    def size(self):
        return self.byte_range[1] - self.byte_range[0]


class StorageAllocator:
    """The StorageAllocator allocates space for files on different storages.
    He tells all parties that want to write a file with a given size, where to write what
    and ensures criterias like capacity and maximal file upload size are met"""

    def __init__(self, storages):
        self.storages = storages

    def best_storage(self):
        return max(self.storages, key=lambda p: p.free_space)

    def allocate_many(self, space):
        """Allocate space for a file among many storages."""
        not_allocated_space = space
        start = 0
        end = 0

        while not_allocated_space > 0:
            storage = self.best_storage()
            allocatable_space = storage.biggest_file()

            storage.allocated_space += allocatable_space
            not_allocated_space -= allocatable_space

            start = end
            end = space - not_allocated_space

            yield StorageAllocation(byte_range=(start, end), storage=storage)

    def allocate(self, space):
        """Ask the StorageAllocator where to write a file with the given space aka allocate space
        :param space: Size of the file that you want to allocate for writing
        """
        total_free_space = sum([p.free_space for p in self.storages])
        if space > total_free_space:
            raise StorageSizeError(message="File with size " + space + "  is too big to store on CuckooDrive."
                                           + "Total free space available is " + total_free_space)
        best_storage = self.best_storage()
        if space <= best_storage.free_space:
            best_storage.allocated_space += space
            return [StorageAllocation(byte_range=(0, space), storage=best_storage)]
        else:
            return list(self.allocate_many(space))
