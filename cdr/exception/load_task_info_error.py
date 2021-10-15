#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3


class LoadTaskInfoError(Exception):

    def __init__(self, msg: str):
        self._msg = msg

    def __str__(self):
        return f"{self._msg}"
