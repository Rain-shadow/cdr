#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-19, 0019 22:33
# @Author: 佚名
# @File  : config.py
import os


class Config:
    CONFIG_DIR_PATH = ".\\config\\"
    DATA_DIR_PATH = ".\\data\\"
    LOG_DIR_PATH = ".\\log\\"
    CDR_VERSION = "1.2.0"

    def __init__(self):
        self.check_dir()

    @staticmethod
    def check_dir():
        if not os.path.exists(Config.CONFIG_DIR_PATH):
            os.mkdir(Config.CONFIG_DIR_PATH)
        if not os.path.exists(Config.DATA_DIR_PATH):
            os.mkdir(Config.DATA_DIR_PATH)
        if not os.path.exists(Config.LOG_DIR_PATH):
            os.mkdir(Config.LOG_DIR_PATH)


__init = Config()
