from __future__ import print_function, division, absolute_import, unicode_literals

from pytest import fixture

from fs.memoryfs import MemoryFS


class StorageProvider:
    pass


class StorageSizeError(Exception):
    pass


class StorageBroker:
    """The StorageBroker decides where files are saved and where they can broker
    read from"""

    def __init__(self, providers):
        self.providers = providers

    def write(self, filesize):
        """Ask the broker where to write a file with the given filesize"""

        def free_space(provider):
            return provider.getmeta("free_space", 0)

        print([free_space(location) for location in self.providers])
        best_location = max(self.providers, key=free_space)
        if(filesize < best_location):
            return [(best_location, (0, filesize))]
        else:
            raise StorageSizeError()


class TestCuckooDriveFS:
    """Test implementation of the CuckooDriveFS"""
    pass


def MB(size):
    return size * 1024 * 1024


class TestStorageBroker:
    @fixture
    def broker(self):
        self.dropbox = MemoryFS()
        self.dropbox._meta["free_space"] = MB(230)
        self.googledrive = MemoryFS()
        self.googledrive._meta["free_space"] = MB(120)

        return StorageBroker(providers=[self.dropbox, self.googledrive])

    def test_write_small_file_returns_location(self, broker):
        #Arrange
        filesize = MB(30)
        #Act
        locations = broker.write(filesize)
        #Assert
        assert (self.dropbox, (0, filesize)) == locations[0]

    def test_write_big_file_returns_multiple_locations_where_to_write_what(self, broker):
        #Arrange
        filesize = MB(330)
        #Act
        locations = broker.write(filesize)
        #Assert
        assert locations == [(self.googledrive, (MB(0), MB(100))),
                             (self.dropbox, (MB(100), MB(200))),
                             (self.dropbox, (MB(200), MB(300))),
                             (self.dropbox, (MB(300), MB(330)))]
