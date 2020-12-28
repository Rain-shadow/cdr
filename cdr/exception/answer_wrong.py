#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-27, 0027 12:25
# @Author: 佚名
# @File  : answer_wrong.py


class AnswerWrong(Exception):

    def __init__(self, data: dict, topic_code: str):
        self._data = data
        self.topic_code = topic_code

    def __str__(self):
        return f"{self._data}"
