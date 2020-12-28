#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-19, 0019 15:29
# @Author: 佚名
# @File  : main.py
from cdr import do_homework, __version__ as cdr_version
from cdr.exception import hook_except
import os
import sys

if __name__ == '__main__':
    os.system(f'title 词达人-v{cdr_version}')
    hook_except()
    do_homework()
    sys.exit(0)
