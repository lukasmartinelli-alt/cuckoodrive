# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from fs.multifs import MultiFS


class WritableMultiFS(MultiFS):
    def best_writefs(self):
        return max(self.fs_sequence, key=lambda fs: fs.getmeta("free_space"))

    def open(self, path, mode='r', buffering=-1, encoding=None, errors=None, newline=None,
             line_buffering=False, **kwargs):
        if 'w' in mode or '+' in mode or 'a' in mode:
            self.setwritefs(self.best_writefs())
        return super(WritableMultiFS, self).open(path, mode, buffering, encoding, errors, newline,
                                             line_buffering)