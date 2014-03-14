# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.path import PathMap, pathjoin


def create_index(fs):
    """Creates an index for the files of a filesystem with the help of PathMap
    The value behind a path is the file information that is provided by the
    filesystem.
    """
    map = PathMap()

    def build(path="/"):
        """Recursively go through the filesystem and add files to the PathMap"""
        for item in fs.listdir(path):
            absolute_path = pathjoin(path, item)
            if(fs.isdir(absolute_path)):
                build(absolute_path)
            else:
                map[absolute_path] = fs.getinfo(absolute_path)

    build()
    return map
