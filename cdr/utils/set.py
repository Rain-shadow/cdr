#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-27, 0027 17:07
# @Author: 佚名
# @File  : set.py


class Set:

    def __init__(self, value: list):
        self.__value = value

    def __and__(self, other):
        tem = []
        teem_map = {}
        for v in self.__value:
            try:
                index = other.__value.index(v, teem_map[v] if teem_map.get(v) else 0)
            except ValueError:
                pass
            else:
                tem.append(v)
                teem_map[v] = index
        return Set(tem)

    def __len__(self):
        return self.__value.__len__()

    def __str__(self):
        return self.__value.__str__()
