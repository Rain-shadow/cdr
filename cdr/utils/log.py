#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-19, 0019 16:15
# @Author: 佚名
# @File  : log.py
import sys
import time
import os
import threading
from cdr.config import LOG_DIR_PATH

__all__ = ["Log"]
_lock = threading.Lock()
_lock.acquire()
__file = open(f"{LOG_DIR_PATH}log.txt", "w", encoding='utf-8')
_lock.release()


def _log(content):
    _lock.acquire()
    __file.write(content)
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
    __ALL_LOGGER = {}

    def __init__(self, name):
        self.__content = list(f"日志名称：{name}\n")
        self.__count = 0
        self.__name = name
        Log.__ALL_LOGGER[name] = self

    @staticmethod
    def get_logger(name: str = threading.currentThread().name):
        if name not in Log.__ALL_LOGGER.keys():
            return Log(name)
        return Log.__ALL_LOGGER[name]

    def __record_log(self, content, end='\n'):
        self.__content.extend(list(str(content)))
        self.__content.extend(list(end))
        self.__count += 1
        if self.__name == threading.main_thread().name \
                and self.__count >= 10:
            self.close()

    def d(self, s, end='\n', is_show=False):
        if is_show and Log.LEVEL <= 0 and Log.DEBUG:
            print(s, end=end)
        self.__record_log(s, end=end)

    def v(self, s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 0:
            print(s, end=end)
        self.__record_log(s, end=end)

    def i(self, s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 1:
            print(f"\033[0;36m[Info]\033[0m {s}", end=end)
        self.__record_log(f"[Info] {s}", end=end)

    def w(self, s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 2:
            print(f"\033[0;33m[Warning] {s}\033[0m", end=end)
        self.__record_log(f"[Warning] {s}", end=end)

    def e(self, s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 3:
            print(f"\033[0;31m[Error] {s}\033[0m", end=end)
        self.__record_log(f"[Error] {s}", end=end)

    def f(self, s, end='\n', is_show=True):
        if is_show and Log.LEVEL <= 4:
            print(s, end=end)
        self.__record_log(s, end=end)

    @staticmethod
    def create_error_txt():
        Log.close_all_logger()
        _create_error_txt()

    @staticmethod
    def close_all_logger():
        for logger in Log.__ALL_LOGGER.values():
            logger.close()
        Log.__ALL_LOGGER.clear()

    def close(self):
        """
        对主线程来说该函数作用仅为更新日志文本
        """
        if self.__name != threading.main_thread().name:
            Log.__ALL_LOGGER[threading.main_thread().name].close()  # 优先刷新主线程日志
            Log.__ALL_LOGGER.pop(self.__name)  # 删除其他日志
        self.__count = 0
        _log("".join(self.__content))
        self.__content.clear()
