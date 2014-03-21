# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals


def mb(value):
    """
    Helper method to return value in MB as value in Bytes
    :param value in Megabytes
    :return: value in Bytes
    """
    return value * 1024 * 1024