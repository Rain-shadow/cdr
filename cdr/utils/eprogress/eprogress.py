#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-29, 0029 12:09
# @Author: HomgWu
# @File  : eprogress.py


"""
Created on 2017/7/21
代码来源于eprogress第三方库
因需自定义部分样式，故基于原码进行微调
"""
__author__ = 'HomgWu'

import sys
import re
import abc
import threading

CLEAR_TO_END = "\033[K"
UP_ONE_LINE = "\033[F"


class ProgressBar(object, metaclass=abc.ABCMeta):
    def __init__(self, width=25, title=''):
        self.width = width
        self.title = ProgressBar.filter_str(title)
        self._lock = threading.Lock()
        self.end = ''

    @property
    def lock(self):
        return self._lock

    @abc.abstractmethod
    def update(self, progress=0, data: dict = None):
        pass

    @abc.abstractmethod
    def finish(self, msg: str = "Finish!"):
        pass

    @staticmethod
    def filter_str(pending_str):
        """去掉字符串中的\r、\t、\n"""
        return re.sub(pattern=r'\r|\t|\n', repl='', string=pending_str)


class CircleProgress(ProgressBar):
    def __init__(self, width=10, title=''):
        """
         @param width : 进度条展示的长度
         @param title : 进度条前面展示的文字
        """
        super(CircleProgress, self).__init__(width=width, title=title)
        self._current_char = ''

    def update(self, progress=0, data=None):
        """
        @param progress : 当前进度值,非0则更新符号
        @param data : 更新部分参数值
        """
        with self.lock:
            if progress > 0:
                self._current_char = CircleProgress._get_next_circle_char(self._current_char)
            if data and data.get("end"):
                self.end = data['end']
            sys.stdout.write('\r' + CLEAR_TO_END)
            sys.stdout.write("\r%s:[%s]   %s" % (self.title, self._current_char, self.end))
            # sys.stdout.flush()

    def finish(self, msg: str = "Finish!"):
        self.update(-1, {"end": msg})

    @staticmethod
    def _get_next_circle_char(current_char):
        if current_char == '':
            current_char = '-'
        elif current_char == '-':
            current_char = '\\'
        elif current_char == '\\':
            current_char = '|'
        elif current_char == '|':
            current_char = '/'
        elif current_char == '/':
            current_char = '-'
        return current_char


class LineProgress(ProgressBar):
    def __init__(self, total=100, symbol='#', width=25, title='', tail="%", is_percent: bool = True):
        """
         @param total : 进度总数
         @param symbol : 进度条符号
         @param width : 进度条展示的长度
         @param title : 进度条前面展示的文字
         @param title : 进度条尾部吧标记符号
        """
        super(LineProgress, self).__init__(width=width, title=title)
        self.total = total
        self.symbol = symbol
        self._current_progress = 0
        self._tail = tail
        self._is_percent = is_percent

    def update(self, progress=0, data=None):
        """
        @param progress : 当前进度值
        @param data : 更新部分参数值
        """
        with self.lock:
            if progress >= 0:
                self._current_progress = progress
            else:
                progress = self._current_progress
            total = self.total
            if self._is_percent:
                progress = self._current_progress * 100 / total
                total = 100
            if data and data.get("tail"):
                self._tail = data["tail"]
            if data and data.get("end"):
                self.end = data['end']
            sys.stdout.write('\r' + CLEAR_TO_END)
            num = int(progress / total * self.width)
            hashes = '◆' * num
            if num != 0:
                hashes = '\033[32m' + hashes
            spaces = '◇' * (self.width - num)
            sys.stdout.write("\r %s:[%s\033[0m%s] %d%s   %s" %
                             (self.title, hashes, spaces, progress, self._tail, self.end))
            # sys.stdout.flush()

    def finish(self, msg: str = "Finish!"):
        self.update(-1, {"end": msg})


class MultiProgressManager(object):
    def __new__(cls, *args, **kwargs):
        """单例"""
        if not hasattr(cls, '_instance'):
            cls._instance = super(MultiProgressManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._progress_dict = {}
        self._lock = threading.Lock()

    def put(self, key, progress_bar):
        with self._lock:
            if key and progress_bar:
                self._progress_dict[key] = progress_bar
                progress_bar.index = len(self._progress_dict) - 1

    def clear(self):
        with self._lock:
            self._progress_dict.clear()

    def update(self, key, progress, data: dict = None):
        """
        @param key : 待更新的进度条标识
        @param progress : 当前进度值
        @param data : 更新部分参数值
        """
        with self._lock:
            if not key:
                return
            delta_line = len(self._progress_dict)
            sys.stdout.write(UP_ONE_LINE * delta_line if delta_line > 0 else '')
            for tmp_key in self._progress_dict.keys():
                progress_bar = self._progress_dict.get(tmp_key)
                tmp_progress = -1
                if key == tmp_key:
                    tmp_progress = progress
                progress_bar.update(tmp_progress, data)
                sys.stdout.write('\n')

    def finish(self, key, msg: str = "Finish!"):
        self.update(key, -1, {"end": msg})
