#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-23, 0023 16:39
# @Author: 佚名
# @File  : __init__.py.py

from .interface import *
from .answer_adapter import AnswerAdapter

adapter = AnswerAdapter()

__all__ = ["adapter"]
