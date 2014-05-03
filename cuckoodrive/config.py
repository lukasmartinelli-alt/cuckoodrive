# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

import os
import yaml


class CuckooConfig(object):
    """
    Encapsulates the configuration of a cuckoo drive. On instantion the configuration file is
    created or loaded and the configuration data can be accessed via the special configuration
    methods.
    """

    template = {
        "include": ["*"],
        "exclude": [".cuckoodrive.yml"],
        "remotes": {}
    }

    def __init__(self, cuckoo_path):
        """Load or create configuration for the given cuckoo drive path"""
        if not os.path.exists(cuckoo_path):
            raise ValueError("Path of cuckoo drive has to exist.")
        if not os.path.isdir(cuckoo_path):
            raise ValueError("Path of cuckoo drive has to be a folder.")

        self.path = os.path.join(cuckoo_path, ".cuckoodrive.yml")
        self.configuration = self.template

        if os.path.exists(self.path):
            self.load()
        else:
            self.save()

    def save(self):
        """
        Save the current configuration to the file.
        This will overwrite the existing file.
        """
        with open(self.path, mode="w") as fh:
            fh.write(yaml.dump(self.configuration))

    def load(self):
        """
        Load the configuration from the cuckoo drive config file.
        """
        with open(self.path, mode="r") as fh:
            self.configuration = yaml.load(fh.read())
