#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-27, 0027 17:07
# @Author: 佚名
# @File  : set.py


class Set:

    def __init__(self, value):
        if isinstance(value, list):
            self.__value = value
        else:
            self.__value = list(value)
        self.__count = 0

    def __and__(self, other):
        tem = []
        tem_map = {}
        for v in self.__value:
            try:
                index = other.__value.index(v, tem_map[v] if tem_map.get(v) else 0)
            except ValueError:
                pass
            else:
                tem.append(v)
                tem_map[v] = index
        return Set(tem)

    def __sub__(self, other):
        tem = self.__value.copy()
        for v in other.__value:
            try:
                tem.remove(v)
            except ValueError:
                pass
        return Set(tem)

    def __iter__(self):
        return self

    def __next__(self):
        if self.__count >= len(self.__value):
            raise StopIteration
        result = self.__value[self.__count]
        self.__count = self.__count + 1
        return result

    def __len__(self):
        return self.__value.__len__()

    def __str__(self):
        return self.__value.__str__()
