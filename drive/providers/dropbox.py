# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from os.path import basename, normpath

from fs.base import FS, synchronize
from fs.errors import ResourceNotFoundError, ResourceInvalidError
from fs.errors import DestinationExistsError
from dropbox import rest


class DropboxFile:
    """A file like interface for the DropboxFS"""
    pass


class DropboxFS(FS):
    """
    Uses the Dropbox Python SDK to read and write via HTTP.
    The implementation is partially based on a solution proposed in the
    pyfilesystem Google Group here: http://bit.ly/OoqXf2
    """
    _meta = {
        "network": True,
        "virtual": False,
        "read_only": False,
        "unicode_paths": True,
        "case_insensitive_paths": False,
        "atomic.move": True,
        "atomic.copy": True,
        "atomic.makedir": True,
        "atomic.rename": True,
        "atomic.setcontents": True,
        "file.read_and_write": False,
    }

    def __init__(self, client, thread_synchronize=True):
        """Create an fs that interacts with Dropbox.
        :param client: Initialized DropboxClient from the SDK
        :param thread_synchronize: set to True to enable thread-safety
        """
        super(DropboxFS, self).__init__(thread_synchronize=thread_synchronize)
        self.client = client

    def __str__(self):
        return "<DropboxFS: %s>" % self.root_path

    def __unicode__(self):
        return u"<DropboxFS: %s>" % self.root_path

    # --------------------------------------------------------------------
    # Essential Methods as defined in
    # https://pythonhosted.org/fs/implementersguide.html#essential-methods
    # --------------------------------------------------------------------
    @synchronize
    def open(self, path, mode="rb", **kwargs):
        path = normpath(path).lstrip('/')
        file = self.client.get_file(path)
        return file

    def isfile(self, path):
        return not self.isdir(path)

    def isdir(self, path):
        info = self.getinfo(path)
        return info.get('is_dir', False)

    def listdir(self, path="/", wildcard=None, full=False, absolute=False,
                dirs_only=False, files_only=False):
        path = normpath(path).lstrip('/')
        try:
            metadata = self.client.metadata(path, list=True)
        except rest.ErrorResponse as e:
            if e.status == 404:
                raise ResourceNotFoundError(path)
            raise
        listing = metadata.get('contents', [])
        listing = [basename(info['path']) for info in listing]
        return self._listdir_helper(path, listing, wildcard, full, absolute,
                                    dirs_only, files_only)

    def makedir(self, path, recursive=False, allow_recreate=False):
        path = normpath(path).lstrip('/')
        try:
            self.client.file_create_folder(path)
        except rest.ErrorResponse as e:
            if e.status == 403 and not allow_recreate:
                raise DestinationExistsError(path)
            raise

    def remove(self, path):
        path = normpath(path).lstrip('/')
        if not self.isfile(path):
            raise ResourceInvalidError(path)
        try:
            self.client.file_delete(path)
        except rest.ErrorResponse as e:
            if e.status == 404:
                raise ResourceNotFoundError(path)
            raise

    def removedir(self, path, recursive=False, force=False):
        path = normpath(path).lstrip('/')
        if not self.isdir(path):
            raise ResourceInvalidError(path)
        try:
            self.client.file_delete(path)
        except rest.ErrorResponse as e:
            if e.status == 404:
                raise ResourceNotFoundError(path)
            raise

    def rename(self, src, dst):
        pass

    def getinfo(self, path):
        path = normpath(path).lstrip('/')
        try:
            info = self.client.metadata(path, list=False)
        except rest.ErrorResponse as e:
            if e.status == 404:
                raise ResourceNotFoundError(path)
            raise
        info['size'] = info.pop('bytes')
        return info

    # ------------------------------------------------------------------------
    # Non-Essential Methods as defined in
    # https://pythonhosted.org/fs/implementersguide.html#non-essential-methods
    # ------------------------------------------------------------------------

    def desc(self, path):
        return "%s in Dropbox" % path

    def exists(self, path):
        try:
            info = self.getinfo(path)
            return 'is_deleted' not in info
        except ResourceNotFoundError:
            return False
