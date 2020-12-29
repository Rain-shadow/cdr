#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-19, 0019 16:15
# @Author: 佚名
# @File  : log.py
import sys
import time
import os
from threading import Lock
from cdr.config import LOG_DIR_PATH

__all__ = ["Log"]
_lock = Lock()
_lock.acquire()
__file = open(f"{LOG_DIR_PATH}log.txt", "w", encoding='utf-8')
_lock.release()


def _log(txt, end='\n'):
    global __file
    _lock.acquire()
    print(txt, file=__file, end=end)
    _lock.release()


def _file_close():
    _lock.acquire()
    __file.close()
    _lock.release()


def _create_error_txt():
    global __file
    _lock.acquire()
    __file.flush()
    sys.stdout.flush()
    __file.close()
    os.system(f'copy {LOG_DIR_PATH}log.txt "{LOG_DIR_PATH}error-'
              f'{time.strftime("%Y-%m-%d-%H.%M.%S", time.localtime())}.txt" > nul')
    os.system(f'copy {LOG_DIR_PATH}log.txt "{LOG_DIR_PATH}error-last.txt" > nul')
    __file = open(f"{LOG_DIR_PATH}log.txt", "a", encoding='utf-8')
    _lock.release()


class Log:
    LEVEL = 0
    DEBUG = True

    @staticmethod
    def d(s, end='\n', is_show=False):
        if is_show and Log.LEVEL <= 0 and Log.DEBUG:
            print(s, end=end)
        _log(s, end=end)

    @staticmethod
    def v(s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 0:
            print(s, end=end)
        _log(s, end=end)

    @staticmethod
    def i(s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 1:
            print(f"\033[0;36m[Info]\033[0m {s}", end=end)
        _log(f"[Info] {s}", end=end)

    @staticmethod
    def w(s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 2:
            print(f"\033[0;33m[Warning] {s}\033[0m", end=end)
        _log(f"[Warning] {s}", end=end)

    @staticmethod
    def e(s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 3:
            print(f"\033[0;31m[Error] {s}\033[0m", end=end)
        _log(f"[Error] {s}", end=end)

    @staticmethod
    def f(s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 4:
            print(s, end=end)
        _log(s, end=end)

    @staticmethod
    def create_error_txt():
        _create_error_txt()

    @staticmethod
    def close():
        _file_close()
