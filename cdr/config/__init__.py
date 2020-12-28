#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-19, 0019 22:33
# @Author: 佚名
# @File  : __init__.py.py

from .config import Config

CONFIG_DIR_PATH = Config.CONFIG_DIR_PATH
CDR_VERSION = Config.CDR_VERSION
DATA_DIR_PATH = Config.DATA_DIR_PATH
LOG_DIR_PATH = Config.LOG_DIR_PATH

__all__ = ["CONFIG_DIR_PATH", "CDR_VERSION", "DATA_DIR_PATH", "LOG_DIR_PATH"]
