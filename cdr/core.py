#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-19, 0019 15:32
# @Author: 佚名
# @File  : core.py
import os
import sys
import time
import cdr.request as requests
from .login import Login
from cdr.config import CDR_VERSION, CONFIG_DIR_PATH
from cdr.test import ClassTask, MyselfTask
from cdr.utils import settings, Log, Tool
from cdr.url import URL


_logger = Log.get_logger()


def do_homework():
    Login()
    URL.load_main()
    #   模拟加载流程
    requests.options("https://app.vocabgo.com/student/", headers=settings.header).close()
    res = requests.get("https://gateway.vocabgo.com/Student/Main?timestamp="
                       f"{Tool.time()}&versions={CDR_VERSION}", headers=settings.header)
    json = res.json()["data"]
    res.close()
    #   模拟加载流程
    requests.get("https://gateway.vocabgo.com/Student/Contest/List?timestamp="
                 f"{Tool.time()}&versions={CDR_VERSION}", headers=settings.header).close()
    timestamp = Tool.time()
    sign = Tool.md5(f'return_url=https%3A%2F%2Fapp.vocabgo.com%2Foverall%2F&timestamp={timestamp}'
                    f'&versions={CDR_VERSION}ajfajfamsnfaflfasakljdlalkflak')
    data = {
        "return_url": "https%3A%2F%2Fapp.vocabgo.com%2Foverall%2F",
        "timestamp": timestamp,
        "versions": CDR_VERSION,
        "sign": sign
    }
    res = requests.post(url='https://gateway.vocabgo.com/Auth/Wechat/Config', headers=settings.header, json=data)
    _logger.i("WechatConfig:")
    _logger.i(res.content.decode("utf8"))
    res.close()
    time.sleep(1)
    #   信息显示
    Tool.cls()
    while True:
        if json['user_info'].get('class_name') is None:
            _logger.v(f"\n{json['user_info']['student_name']}（未加入班级）\n")
        else:
            _logger.v(f"\n{json['user_info']['student_name']}（{json['user_info']['class_name']}）\n")
        _logger.v("1.班级任务\n2.自选任务\n3.删除本地授权信息（可更换账号刷题）"
                  "\n4.打开配置文件（关闭后将自动重载配置文件，记得保存）"
                  "\n\n#.加群1085739587免费获取最新版，更少的BUG、更高的准确率\n\n0.退出\n")
        settings.save()
        choose = input("请输入序号：")
        if choose == "1":
            _logger.i("正在加载任务列表中，请稍等......")
            ClassTask().run()
            Tool.cls()
        elif choose == "2":
            _logger.i("正在加载任务列表中，请稍等......")
            URL.load_myself_task_list()
            MyselfTask(json['user_info']['course_id']).run()
            Tool.cls()
        elif choose == "3":
            settings.user_token = ""
            settings.save()
            Login()
            Tool.cls()
            res = requests.get("https://gateway.vocabgo.com/Student/Main?timestamp="
                               f"{Tool.time()}&versions={CDR_VERSION}", headers=settings.header)
            json = res.json()["data"]
            res.close()
        elif choose == "4":
            os.system(f'notepad {CONFIG_DIR_PATH + "config.txt"}')
            settings.reload()
            Tool.cls()
        elif choose == "0":
            sys.exit(0)
        else:
            Tool.cls()
            _logger.i("输入格式有误！\n")
        res = requests.get("https://gateway.vocabgo.com/Student/Main?timestamp="
                           f"{Tool.time()}&versions={CDR_VERSION}", headers=settings.header)
        json = res.json()["data"]
        res.close()
