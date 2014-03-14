# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.base import FS


class GoogleDriveFS(FS):
    """
    Uses the Google Drive Python Client API to read and write via HTTP
    to Google Drive.
    """
    API_KEY = ".".join(["881568171821-15mmg2at5uqoqhss387ja288ar9tvanp",
                       "apps", "googleusercontent", "com"])
    API_SECRET = "omKBTiKR5nOCUWhWLJoPdYBT"

    _meta = {
        "network": True,
        "read_only": False
    }

    def __init__(self, client, thread_synchronize=True):
        """Create an fs that interacts with GoogleDrive.
        :param client: Built Google Drive Service from the SDK
        :param thread_synchronize: set to True to enable thread-safety
        """
        super(GoogleDriveFS, self).__init__(thread_synchronize=thread_synchronize)
        self.client = client

    def __str__(self):
        return "<GoogleDriveFS: %s>" % self.root_path

    def __unicode__(self):
        return u"<GoogleDriveFS: %s>" % self.root_path

    # --------------------------------------------------------------------
    # Essential Methods as defined in
    # https://pythonhosted.org/fs/implementersguide.html#essential-methods
    # --------------------------------------------------------------------
