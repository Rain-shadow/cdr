#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-19, 0019 15:29
# @Author: 佚名
# @File  : main.py
from cdr import do_homework, __version__ as cdr_version
from cdr.exception import hook_except
from cdr.utils import Log
import ctypes
import os
import sys


def version():
    return cdr_version


if __name__ == '__main__':
    if len(sys.argv[1:]) != 0 and sys.argv[1:][0] == "-v":
        print(version())
        from cdr.aio import aiorequset
        aiorequset.close_session()
        sys.exit(0)

    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
    os.system(f'title 词达人-v{cdr_version}')
    hook_except()
    Log.get_logger().i(f"词达人版本：{cdr_version}", is_show=False)
    do_homework()
    sys.exit(0)
