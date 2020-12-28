#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-19, 0019 15:32
# @Author: 佚名
# @File  : core.py
# cython: language_level=3
# -*- coding: utf-8 -*-
import requests
import sys
import time
from .login import Login
from .config import CDR_VERSION
from .utils import settings, Log, Tool
from .test import ClassTask, MyselfTask


def do_homework():
    Login()
    #   模拟加载流程
    requests.get("https://app.vocabgo.com/overall/#/student", headers=settings.header).close()
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
    res = requests.post(url='https://gateway.vocabgo.com/Auth/Wechat/Config',
                        headers=settings.header, json=data)
    Log.i("WechatConfig:")
    Log.i(res.content.decode("utf8"))
    res.close()
    time.sleep(1)
    #   信息显示
    Tool.cls()
    while True:
        if json['user_info'].get('class_name') is None:
            Log.v(f"\n{json['user_info']['student_name']}（未加入班级）\n")
        else:
            Log.v(f"\n{json['user_info']['student_name']}（{json['user_info']['class_name']}）\n")
        Log.v("1.班级任务\n2.自选任务\n3.删除本地授权信息（可更换账号刷题）\n\n0.退出\n")
        choose = input("请输入序号：")
        if choose == "1":
            Log.i("正在加载任务列表中，请稍等......")
            ClassTask().run()
            Tool.cls()
        elif choose == "2":
            Log.i("正在加载任务列表中，请稍等......")
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
        elif choose == "0":
            sys.exit(0)
        else:
            Tool.cls()
            Log.i("输入格式有误！\n")
