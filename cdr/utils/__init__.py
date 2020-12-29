#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-19, 0019 16:15
# @Author: 佚名
# @File  : __init__.py.py

from .log import Log
from .set import Set
from .setting import Settings, _settings
from .course import Course
from .answer import Answer
from .tool import Tool

settings = _settings

__all__ = ["Log", "settings", "Set", "Settings", "Course", "Answer", "Tool"]
