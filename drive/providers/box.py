# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from os.path import normpath

from fs.base import FS, synchronize


class BoxFS(FS):
    API_KEY = "qng59eaxirseii3afyvu586td2wev40k"
    API_SECRET = "g2axxUcHpGF5qFQIbF2WLUXZWPqc8lE1"
    API_DEV_TOKEN = "mgdWbMJygF66xarW6dZSYZvq1GmSLXf7"

    _meta = {
        "network": True,
        "read_only": False
    }

    def __init__(self, client, thread_synchronize=True):
        """Create a filesystem that interacts with Box.
        :param client: Already connected BoxClient
        :param thread_synchronize: set to True to enable thread-safety
        """
        super(BoxFS, self).__init__(thread_synchronize=thread_synchronize)
        self.client = client

    def __str__(self):
        return "<BoxFS: %s>" % self.root_path

    def __unicode__(self):
        return u"<BoxFS: %s>" % self.root_path

    # --------------------------------------------------------------------
    # Essential Methods as defined in
    # https://pythonhosted.org/fs/implementersguide.html#essential-methods
    # --------------------------------------------------------------------
    @synchronize
    def open(self, path, mode="rb", **kwargs):
        path = normpath(path).lstrip('/')
        file = self.client.download_file(path)
        return file

    def isfile(self, path):
        return not self.isdir(path)

    def isdir(self, path):
        info = self.getinfo(path)
        return info.get('is_dir', False)
