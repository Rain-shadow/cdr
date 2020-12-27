#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-20, 0020 22:45
# @Author: 佚名
# @File  : login.py
import requests
import time
import sys
import os
import random
import qrcode
from cdr.utils import settings, Log, Tool
from cdr.config import CDR_VERSION, CONFIG_DIR_PATH


class Login:

    def __init__(self):
        Tool.cls()
        if settings.user_token != "0" and settings.user_token != "":
            Log.i("尝试复用token")
            res = requests.get(url='https://gateway.vocabgo.com/Student/Main?timestamp={}&versions={}'
                               .format(Tool.time(), CDR_VERSION), headers=settings.header)
            code = res.json()["code"]
            res.close()
            if code == 1:
                Log.i("授权成功")
                Log.i("user_token:" + settings.user_token, is_show=False)
                return
            else:
                Log.i("曾用token已失效，重新执行授权流程！")
        Login._generate_qr_code()
        res = requests.get(url='https://gateway.vocabgo.com/Student/Main?timestamp={}&versions={}'
                           .format(Tool.time(), CDR_VERSION), headers=settings.header)
        code = res.json()["code"]
        res.close()
        count = 0
        while code != 1:
            Log.i("等待授权中......")
            count = count + 1
            time.sleep(5)
            if count == 6:
                count = 0
                Log.i("1. 继续等待\n2. 重新生成二维码\n\n0. 返回上一级")
                code_type = input("请输入指令：")
                if code_type == "1":
                    continue
                elif code_type == "2":
                    Login._generate_qr_code()
                    continue
                elif code_type == "0":
                    return
                else:
                    sys.exit(0)
            res = requests.get(url='https://gateway.vocabgo.com/Student/Main?timestamp={}&versions={}'
                               .format(Tool.time(), CDR_VERSION), headers=settings.header)
            code = res.json()["code"]
            res.close()
        Log.i("授权成功")
        os.remove(f"{CONFIG_DIR_PATH}授权二维码.jpg")
        settings.save()
        return

    @staticmethod
    def _generate_qr_code():
        user_agent = settings.user_agent
        user_token = settings.user_token
        now_time = Tool.time()  # 获取13位时间戳

        # 生成token
        pass_list = 'abcde0123456789'
        for _ in range(0, 32):
            index = random.randint(0, len(pass_list) - 1)
            user_token += pass_list[index]
        user_token = Tool.md5(f"{user_token}{Tool.time()}")
        # 生成token认证连接
        sign = Tool.md5(f'auth_type=1&return_url=https://app.vocabgo.com/overall/#/student/home&timestamp={now_time}'
                        + f'&user_token={user_token}&versions={CDR_VERSION}ajfajfamsnfaflfasakljdlalkflak')
        data = {
            "return_url": "https://app.vocabgo.com/overall/#/student/home",
            "auth_type": 1,
            "user_token": user_token,
            "timestamp": now_time,
            "versions": CDR_VERSION,
            "sign": sign
        }
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Host': 'app.vocabgo.com',
            'Origin': 'https://app.vocabgo.com',
            'Referer': 'https://app.vocabgo.com/',
            'User-Agent': user_agent,
            # TODO 似乎是md5值，回头随机一个测试康康
            # 'D9886F0A0D37C25B2E9998FEC289C919'
            'X-DevTools-Emulate-Network-Conditions-Client-Id': Tool.md5(user_agent).upper(),
            'X-Requested-With': 'XMLHttpRequest'
        }
        Log.i(f'https://gateway.vocabgo.com/Auth/Thirdpart/Authorize?{data}')
        res = requests.post(url='https://gateway.vocabgo.com/Auth/Thirdpart/Authorize', headers=headers, json=data)
        json_str1 = res.json()
        res.close()
        login_url = json_str1['data']['redirect_url']
        Log.i("user_token:" + user_token)
        settings.user_token = user_token
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=1
        )  # 设置二维码的大小
        qr.add_data(login_url)
        qr.make(fit=True)
        img = qr.make_image()
        Log.i("二维码以生成，将自动展示，请使用微信扫一扫进行词达人授权。成功后请关闭图片查看程序，若失败，用户可在“main目录\\config目录”下找到“授权二维码.jpg”")
        img.save(f"{CONFIG_DIR_PATH}授权二维码.jpg")
        img.show()  # 显示图片

