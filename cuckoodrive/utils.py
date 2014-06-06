# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals


def kb(value):
    """
    Helper method to return value in KB as value in Bytes
    :param value in Kilobytes
    :return: value in Bytes
    """
    return value * 1024


def mb(value):
    """
    Helper method to return value in MB as values in Bytes
    """
    return kb(value) * 1024
