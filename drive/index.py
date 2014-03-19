# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.path import PathMap, pathjoin


class Index(PathMap):
    def __init__(self, fs):
        """Creates an index for the files of a filesystem with the help of PathMap
        The value behind a path is the file information that is provided by the
        filesystem.
        """
        PathMap.__init__(self)
        self.fs = fs
        self._build()

    def _build(self, path="/"):
        """Recursively go through the filesystem and add files to the PathMap"""
        for item in self.fs.listdir(path):
            absolute_path = pathjoin(path, item)
            if self.fs.isdir(absolute_path):
                self._build(absolute_path)
            else:
                self[absolute_path] = self.fs.getinfo(absolute_path)
