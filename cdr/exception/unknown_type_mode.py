#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Author: 佚名

class UnknownTypeMode(Exception):

    def __init__(self, type_mode: int):
        self.__type_mode = type_mode

    def __str__(self):
        return f"未知题型：{self.__type_mode}"
