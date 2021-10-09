#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2021-01-15, 0015 21:38
# @Author: 佚名
# @File  : verification_code.py
import asyncio
import base64
import io
import os

from PIL import Image
from cdr.config import CONFIG_DIR_PATH
from cdr.utils.log import Log
from cdr.utils.setting import _settings as settings

_logger = Log.get_logger()


class VerificationCode:

    @staticmethod
    async def get_vc(img_base64: str, task_id, fail_times: int):
        img_b64decode = base64.b64decode(img_base64)  # base64解码
        image = io.BytesIO(img_b64decode)
        img = Image.open(image)
        img_path = f"{CONFIG_DIR_PATH}验证码-{task_id}.png"
        img.save(img_path)
        code = None
        if fail_times > settings.verify_times:
            code = await VerificationCode.default(img_base64, img_path, task_id)
        else:
            try:
                models = __import__("custom_verification")
                code = await models.CustomVerification.get_vc(img_base64, img_path, task_id)
            except (ModuleNotFoundError, AttributeError, TypeError) as e:
                _logger.w(e, is_show=False)
                code = await VerificationCode.default(img_base64, img_path, task_id)
            except Exception as e:
                _logger.w("自定义验证码出现未知异常")
                _logger.w(e)
            else:
                _logger.i(f"自定义识别结果：{code}")
        os.remove(f"{CONFIG_DIR_PATH}验证码-{task_id}.png")
        return code

    @staticmethod
    async def default(img_base64: str, img_path: str, task_id):
        _logger.i("验证码即将展示，若看不清可输入-1重新生成")
        loop = asyncio.get_event_loop()
        proc = await asyncio.create_subprocess_shell(f"start {CONFIG_DIR_PATH}验证码-{task_id}.png", loop=loop)
        await proc.communicate()
        code = input(f"验证码-{task_id}：")
        return code
