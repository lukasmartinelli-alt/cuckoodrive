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

    def free_space(self):
        return self.fs.max_size - self.fs.cur_size


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

    def allocate(self, filesize):
        """Ask the StorageAllocator where to write a file with the given filesize aka allocate space
        :param filesize: Size of the file that you want to allocate for writing
        """
        best_location = max(self.providers, key=lambda p: p.free_space())

        if filesize < best_location.free_space():
            return [StorageAllocation(byte_range=(0, filesize), storage=best_location)]
        else:
            raise StorageSizeError(message="Required allocation for filesize was too large.", storage_name=best_location.name,
                                   free_space=best_location.free_space(), required_space=filesize)