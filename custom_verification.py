#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2021-01-15, 0015 21:38
# @Author: 佚名
# @File  : custom_verification.py
import requests
import aiohttp

# 获取词达人配置目录路径
from cdr.config import CONFIG_DIR_PATH
# 获取词达人日志记录实例
from cdr.utils.log import Log

_r = aiohttp.ClientSession()
_logger = Log.get_logger()


#  该类名不得修改
class CustomVerification:

    #  该函数名不得修改
    @staticmethod
    async def get_vc(img_base64: str, img_path: str, task_id):
        """
        自定义验证码机制，前三次识别交由用户去实现验证码识别
        :param img_base64: 图片的base64编码，格式为png
        :param img_path: 图片的本地路径
        :param task_id: 任务id，一般不用
        :return: 验证码字符串，返回-1将重新生成验证码
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "image": f"data:image/png;base64,{img_base64}",
            "type": "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic",
            "detect_direction": False,
            "language_type": "ENG"
        }
        res = await _r.post("https://ai.baidu.com/aidemo", headers=headers, data=data)
        json_data = await res.json(content_type="text/json")
        if json_data["data"]["words_result_num"] == 0:
            return "-1"
        code = json_data["data"]["words_result"][0]["words"]
        return "".join(code.split())
