#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2021-01-5, 0005 14:43
# @Author: 佚名
# @File  : upper_limit_error.py


class UpperLimitError(Exception):

    def __init__(self, code: int, url, msg):
        self.code = code
        self.url = url
        self.msg = msg

    def __str__(self):
        return f"答词上限:\ncode:{self.code}\nurl:{self.url}\nmsg:{self.msg}"
