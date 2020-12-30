#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-30, 0030 16:53
# @Author: 佚名
# @File  : network_error.py


class NetworkError(Exception):

    def __init__(self, code: int, url, text):
        self.code = code
        self.url = url
        self.msg = text

    def __str__(self):
        return f"网络请求未成功:\ncode:{self.code}\nurl:{self.url}\nmsg:{self.msg}"
