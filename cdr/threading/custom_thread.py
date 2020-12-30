#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-29, 0029 15:26
# @Author: 佚名
# @File  : custom_thread.py
import sys as _sys
from threading import Thread
from traceback import format_exc as _format_exc


# noinspection PyBroadException
class CustomThread(Thread):
    _exc_info = _sys.exc_info

    def __init__(self, target, args=()):
        super(CustomThread, self).__init__(target=target, args=args)

    def run(self) -> None:
        try:
            super(CustomThread, self).run()
        except BaseException:
            if _sys:
                if id(_sys.excepthook) != id(_sys.__excepthook__):
                    exc_type, exc_value, exc_tb = self._exc_info()
                    _sys.excepthook(exc_type, exc_value, exc_tb)
                else:
                    _sys.stderr.write("Exception in thread %s:\n%s\n" %
                                      (self.getName(), _format_exc()))
