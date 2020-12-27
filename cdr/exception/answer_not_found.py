#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-23, 0023 22:57
# @Author: 佚名
# @File  : answer_not_found.py


class AnswerNotFoundException(Exception):

    def __init__(self, mode: int):
        self.__mode = mode

    def __str__(self):
        return f"题型{self.__mode}答案查询出错！"
