#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-23, 0023 22:57
# @Author: 佚名


class NoSupportVersionException(Exception):

    def __init__(self, type_mode: str, version: int):
        self.__type = type_mode
        self.__version = version

    def __str__(self):
        return f"不支持的【{self.__type}】协议，协议版本号：{self.__version}"
