from __future__ import print_function, division, absolute_import, unicode_literals


class CuckooDriveFS:
    pass


class StorageProvider:
    """A storage provider is a remote filesystem where you can write to"""

    def __init__(self, name, fs):
        """
        Create a new storage provider with an underlying remote filesystem
        :param fs: Underlying filesystem of the StorageProvider
        :param name: Name of the StorageProvider
        """
        self.fs = fs
        self.name = name
        self.allocated_space = 0

    def free_space(self):
        return self.fs.max_size - self.fs.cur_size - self.allocated_space


class StorageSizeError(Exception):
    """Exception that is raised if a storage provider has no more space left, even though
    more space is required"""

    def __init__(self, message, storage_name, free_space, required_space):
        """
        Create new error
        :param message: Why the error was raised
        :param storage_name: Provider where the error occured
        :param free_space: Free space of the provier
        :param required_space: Space that would have been required to fulfill the requirement
        """
        Exception.__init__(self, message)
        self.required_space = required_space
        self.free_space = free_space
        self.provider = storage_name


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


class StorageAllocator:
    """The StorageAllocator allocates space for files on different storages.
    He tells all parties that want to write a file with a given size, where to write what
    and ensures criterias like capacity and maximal file upload size are met"""

    def __init__(self, providers):
        self.providers = providers

    def best_storage(self):
        return max(self.providers, key=lambda p: p.free_space())

    def allocate_many(self, filesize):
        max_filesize = 100 * 1024 * 1024
        start = 0
        end = filesize

        while end <= filesize:
            storage = self.best_storage()
            storage.allocated_space += end - start
            yield StorageAllocation((start, end), storage)
            start = end
            end += max_filesize

    def allocate(self, filesize):
        """Ask the StorageAllocator where to write a file with the given filesize aka allocate space
        :param filesize: Size of the file that you want to allocate for writing
        """
        available_space = sum([p.free_space() for p in self.providers])
        if filesize > available_space:
            raise StorageSizeError(message="File is to big to split up and allocate on differents storages",
                                   storage_name=",".join(self.providers),
                                   free_space=available_space, required_space=filesize)

        best_storage = self.best_storage()
        if filesize > best_storage:
            best_storage.allocated_space += filesize
            return [StorageAllocation(byte_range=(0, filesize), storage=best_storage)]
        else:
            return list(self.allocate_many(filesize))
