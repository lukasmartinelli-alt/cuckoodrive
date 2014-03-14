# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.base import FS


class BoxFS(FS):
    _meta = {
        "network": True,
        "read_only": False
    }

    # --------------------------------------------------------------------
    # Essential Methods as defined in
    # https://pythonhosted.org/fs/implementersguide.html#essential-methods
    # --------------------------------------------------------------------
