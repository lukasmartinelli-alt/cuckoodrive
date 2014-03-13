# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.base import FS


class OneDriveFS(FS):
    API_KEY = "0000000040117B19"
    API_SECRET = "0rfqoEaxKjG10DiqbVxCSnSkR7dIUTFp"

    _meta = {
        "network": True,
        "read_only": False
    }

    def __init__(self, client, thread_synchronize=True):
        """Create an fs that interacts with GoogleDrive.
        :param client: Built Google Drive Service from the SDK
        :param thread_synchronize: set to True to enable thread-safety
        """
        super(OneDriveFS, self).__init__(thread_synchronize=thread_synchronize)
        self.client = client

    def __str__(self):
        return "<OneDriveFS: %s>" % self.root_path

    def __unicode__(self):
        return u"<OneDriveFS: %s>" % self.root_path
