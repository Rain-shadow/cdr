#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2021-01-15, 0015 21:38
# @Author: 佚名
# @File  : verification_code.py
import base64
import io
import matplotlib.pyplot as plt
from PIL import Image
from cdr.config import CONFIG_DIR_PATH


class VerificationCode:

    @staticmethod
    def get_vc(img_base64: str, task_id):
        img_b64decode = base64.b64decode(img_base64)  # base64解码

        image = io.BytesIO(img_b64decode)
        img = Image.open(image)
        img.save(f"{CONFIG_DIR_PATH}验证码-{task_id}.png")
        plt.imshow(img)
        plt.show()
        return input(f"验证码-{task_id}：")
