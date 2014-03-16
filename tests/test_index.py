from __future__ import print_function, division, absolute_import, unicode_literals

from os import urandom

from pytest import fixture

from fs.memoryfs import MemoryFS
from drive.index import Index


@fixture
def test_fs():
    fs = MemoryFS()

    def create_file(path, size):
        with fs.open(path, "wb") as file:
            file.write(urandom(size))

    fs.makedir("Backups")
    create_file("Backups/backup-2014-01-14.tar.gz", 130 * 1024)
    create_file("Backups/backup-2014-02-21.tar.gz", 180 * 1024)
    create_file("Backups/backup-2014-03-02.tar.gz", 240 * 1024)

    fs.makedir("Photos")
    fs.makedir("Photos/My Birthday Party")
    create_file("Photos/My Birthday Party/eating_cake.jpg", 5 * 1024)
    create_file("Photos/My Birthday Party/drinking_beer.jpg", 6 * 1024)
    create_file("Photos/My Birthday Party/dancing_around.jpg", 4 * 1024)

    fs.makedir("Archive")

    create_file("My_essay.doc", 680)
    create_file("readme.txt", 58)

    return fs


def test_create_index_returns_pathmap_with_files(test_fs):
    #Act
    index = Index(test_fs)
    #Assert
    assert 8 == len(list(index.iterkeys()))


def test_create_index_returns_pathmap_with_stored_fileinfo(test_fs):
    #Arrange
    filesize = 4 * 1024
    #Act
    index = Index(test_fs)
    #Assert
    info = index["Photos/My Birthday Party/dancing_around.jpg"]
    assert filesize == info['size']
