# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from fs.path import splitext
from fs.wrapfs import WrapFS


class ZipCompressionFS(WrapFS):
    """
    The ZipCompressionFS creates a ZipFile for every single file given but retains the normal folder
    structure. This does not result in the best compression, because we would have mor
    redundancy when we would compress bigger chunks, but has other useful features.
    """

    _meta = {
        "virtual": True,
        "read_only": False,
        "unicode_paths": True,
        "case_insensitive_paths": False
    }

    def __init__(self, fs):
        super(ZipCompressionFS, self).__init__(fs)

    def _encode(self, path):
        return "{0}.zip".format(path)

    def _decode(self, path):
        return splitext(path)[0]