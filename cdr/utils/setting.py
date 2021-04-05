#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-19, 0019 19:15
# @Author: 佚名
# @File  : setting.py

import os
import json
import chardet
import threading
from cdr.config import CONFIG_DIR_PATH
from .log import Log


_logger = Log.get_logger()


def _get_encode_info(file):
    with open(file, 'rb') as f:
        return chardet.detect(f.read())['encoding']


class Settings(object):
    VERSION = 7
    _instance_lock = threading.Lock()

    def __init__(self):
        self.user_token = ""
        self.user_agent = ""
        self._is_random_time = True
        self._is_random_score = False
        self._is_style_by_percent = True
        self._multiple_task = 1
        self._min_random_time = 5
        self._max_random_time = 12
        self._base_score = 90
        self._offset_score = 1
        self.version = Settings.VERSION - 1
        self._note = ""
        self.timeout = 30
        self.reload(True)

    def __new__(cls, *args, **kwargs):
        """单例"""
        if not hasattr(cls, '_instance'):
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    def save(self):
        s_json = {
            "userToken": self.user_token,
            "userAgent": self.user_agent,
            "isRandomTime": self.is_random_time,
            "isRandomScore": self.is_random_score,
            "isStyleByPercent": self.is_style_by_percent,
            "multipleTask": self._multiple_task,
            "minRandomTime": self.min_random_time,
            "maxRandomTime": self.max_random_time,
            "baseScore": self.base_score,
            "offsetScore": self.offset_score,
            "version": self.version,
            "#": self._note
        }
        with open(CONFIG_DIR_PATH + "config.txt", mode='w', encoding='utf-8') as cfg:
            cfg.write(json.dumps(s_json, indent=2, ensure_ascii=False))

    def reload(self, is_init=False):
        if not is_init:
            _logger.i("重新加载配置文件中......")
        if os.path.exists(CONFIG_DIR_PATH + "config.txt"):
            with open(CONFIG_DIR_PATH + "config.txt", mode='r',
                      encoding=_get_encode_info(CONFIG_DIR_PATH + "config.txt")) as cfg:
                tem = cfg.read().encode('utf-8').decode('utf-8')
            if _get_encode_info(CONFIG_DIR_PATH + "config.txt") != "utf-8":
                _logger.w("检测到配置文件格式有误，自动转换文件格式")
                with open(CONFIG_DIR_PATH + "config.txt", mode='w', encoding='utf-8') as cfg:
                    cfg.write(tem)
            s_json = json.loads(tem)
        else:
            s_json = {
                "userToken": "0",
                "userAgent": 'Mozilla/5.0 (Linux; Android 10; COL-AL10 Build/HUAWEICOL-AL10; wv) AppleWebKit/537.36 '
                             '(KHTML, like Gecko) Version/4.0 Chrome/66.0.3359.126 MQQBrowser/6.2 '
                             'TBS/045131 Mobile Safari/537.36 MMWEBID/8465 MicroMessenger/7.0.13.1640(0x27000D39) '
                             'Process/tools NetType/WIFI Language/zh_CN ABI/arm64 WeChat/arm64',
                "isRandomTime": True,
                "isRandomScore": False,
                "isStyleByPercent": True,
                "multipleTask": 1,
                "minRandomTime": 5,
                "maxRandomTime": 12,
                "baseScore": 91,
                "offsetScore": 1,
                "version": Settings.VERSION - 1
            }
        if s_json.get("version") is None or s_json["version"] < Settings.VERSION:
            s_json = self.update_config(s_json["version"], s_json)
            s_json["version"] = Settings.VERSION
            s_json["#"] = [
                "该列表为上方配置的注释项",
                "修改配置文件后，需要重启程序才能使新的配置项生效",
                "不保证100%准确率，在测试的《四级核心词汇1-4》中，目前已发现4道题人工做也无法分辨答案，遇见这种题答对概率只有50%",
                "userToken: 用户身份标识，记录在本地后可以让用户不必次次进行扫码授权",
                "userAgent: UA，用于伪装你在手机上答题，反应你所使用的操作系统/浏览器环境/硬件，没有相关知识请勿修改",
                "isRandomTime: 是否开启随机提交时间，关闭后默认以100ms速度一道题提交。取值[true/false]",
                "警告！应当只有在任务离结束不到10分钟时再关闭，关闭后被词达人封1天的概率是100%，但任务能快速完成，请各位自行抉择",
                "PS:现在不封号，改弹验证码了",
                "警告！关闭该项会造成控分系统出现巨大误差，会让实际分数远高于目标分数（当然不可能超过100）",
                "isRandomScore: 是否开启控分选项，实际成绩总是略高于目标分数，但不超过100。取值[true/false]",
                "isStyleByPercent: 在多任务中是否让进度条以百分比显示，对于任务量较重的建议关闭，将以具体数量显示。取值[true/false]",
                "multipleTask: 同时进行的任务数量，最低为1，最大为6，若格式错误将重置为1",
                "警告！该功能为实验性功能，或许会存在未知BUG！请谨慎开启！",
                "警告！虽在个人测试中未有封号现象，但无法保证该现象为普遍现象，更无法保证以后也如此，请谨慎开启！",
                "maxRandomTime: 最大随机时间，其值不得小于minRandomTime，单位：秒",
                "minRandomTime: 最小随机时间，其值不得大于maxRandomTime，单位：秒",
                "最大时间不得大于35，否则设置无法生效，将使用每个题型的最大时间",
                "注意，随机时间过小会被词达人风控系统检测，然后疯狂弹验证码，请勿将最小时间设置太小",
                "baseScore: 以其为基准为，offsetScore为波动范围进行成绩随机。取值容许小数",
                "offsetScore: 开启随机分数后的偏差值。取值容许小数",
                "目标分数 ∈ [baseScore - offsetScore, baseScore + offsetScore]",
                "version: 配置文件版本，该项用户不得更改，此值会作为是否更新config文件的依据",
                "词达人官方限制一天最多答3k题量，若老师发布任务较重，请勿堆积至一天内完成",
                "若修改配置文件导致程序异常，请删除config.txt文件再运行一次程序使其重新生成即可正常运行"
            ]
        self.user_token = s_json["userToken"]
        self.user_agent = s_json["userAgent"]
        self.is_random_time = s_json["isRandomTime"]
        self.is_random_score = s_json["isRandomScore"]
        self.is_style_by_percent = s_json["isStyleByPercent"]
        self.multiple_task = s_json["multipleTask"]
        self.min_random_time = s_json["minRandomTime"]
        self.max_random_time = s_json["maxRandomTime"]
        self.base_score = s_json["baseScore"]
        self.offset_score = s_json["offsetScore"]
        self.version = s_json["version"]
        self._note = s_json["#"]
        self.timeout = 30
        self.save()

    @staticmethod
    def update_config(version: int, json_config: dict) -> dict:
        if version < 6:
            json_config["multipleTask"] = 1
        if version < 7:
            json_config["isStyleByPercent"] = True
        return json_config

    @property
    def header(self):
        headers = {
            "Host": "gateway.vocabgo.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Requested-With": "XMLHttpRequest",
            "UserToken": self.user_token,
            "User-Agent": self.user_agent,
            "Origin": "https://app.vocabgo.com",
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=utf-8",
            "Referer": "https://app.vocabgo.com/overall/",
            "TE": "Trailers"
        }
        return headers

    @property
    def is_random_time(self) -> bool:
        return self._is_random_time

    @is_random_time.setter
    def is_random_time(self, value):
        if isinstance(value, bool):
            self._is_random_time = value
        else:
            self._is_random_time = True

    @property
    def is_random_score(self) -> bool:
        return self._is_random_score

    @is_random_score.setter
    def is_random_score(self, value):
        if isinstance(value, bool):
            self._is_random_score = value
        else:
            self._is_random_score = False

    @property
    def is_style_by_percent(self):
        return self._is_style_by_percent

    @is_style_by_percent.setter
    def is_style_by_percent(self, value):
        if isinstance(value, bool):
            self._is_style_by_percent = value
        else:
            self._is_style_by_percent = True

    @property
    def is_multiple_task(self) -> bool:
        return self.multiple_task != 1

    @property
    def multiple_task(self):
        return self._multiple_task

    @multiple_task.setter
    def multiple_task(self, value):
        if not isinstance(value, int):
            self._multiple_task = 1
        else:
            if value > 6 or value < 1:
                self._multiple_task = 1
            else:
                self._multiple_task = value

    @property
    def min_random_time(self):
        return self._min_random_time

    @min_random_time.setter
    def min_random_time(self, value):
        if not isinstance(value, int) and not isinstance(value, float):
            self._min_random_time = 5
        else:
            if value > 20 or value < 0.2:
                self._min_random_time = 5
            else:
                self._min_random_time = value

    @property
    def max_random_time(self):
        return self._max_random_time

    @max_random_time.setter
    def max_random_time(self, value):
        if not isinstance(value, int) and not isinstance(value, float):
            self._max_random_time = 12
        else:
            if value <= self.min_random_time:
                self._max_random_time = self._min_random_time + 10
            else:
                self._max_random_time = value

    @property
    def base_score(self):
        return self._base_score

    @base_score.setter
    def base_score(self, value):
        if not isinstance(value, int) and not isinstance(value, float):
            self._base_score = 91
        else:
            self._base_score = value

    @property
    def offset_score(self):
        return self._offset_score

    @offset_score.setter
    def offset_score(self, value):
        if not isinstance(value, int) and not isinstance(value, float):
            self._offset_score = 1
        else:
            self._offset_score = value


_settings = Settings()
__all__ = ["Settings", "_settings"]
