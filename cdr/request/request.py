#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-30, 0030 16:09
# @Author: 佚名
# @File  : request.py
import re
from json import JSONDecodeError

import requests
import urllib3
from requests.adapters import HTTPAdapter

from cdr.utils import Log
from .network_error import NetworkError
from .upper_limit_error import UpperLimitError

_logger = Log.get_logger()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__s = requests.Session()
__s.mount('http://', HTTPAdapter(max_retries=15))
__s.mount('https://', HTTPAdapter(max_retries=15))
__s.adapters.DEFAULT_RETRIES = 15
# __s.keep_alive = False


def __judge_code(res: requests.models.Response) -> requests.models.Response:
    try:
        content = res.content.decode("utf-8")
        if re.match(r".+?\.(?:css|js)(\?.+)?$", res.url) is None and content.find("<html") == -1:
            _logger.i(content, is_show=False)
    except UnicodeDecodeError:
        # _logger.i(res.content, is_show=False)
        pass
    if res.status_code != 200:
        if res.url != "https://app.vocabgo.com/student/":
            raise NetworkError(res.status_code, res.url, res.content.decode("utf-8"))
    else:
        try:
            json_data = res.json()
        except JSONDecodeError:
            pass
        else:
            if res.url.find("gateway.vocabgo.com") != -1:
                if json_data and (json_data["code"] == 0 or json_data["code"] == 10002
                                  or json_data["code"] == 21006):
                    _logger.e(f"{json_data['code']}, {res.url}, {json_data['msg']}", is_show=False)
                if json_data and json_data["code"] == 10017:
                    raise UpperLimitError(res.status_code, res.url, json_data["msg"])
    return res


def options(url, **kwargs):
    return __judge_code(__s.options(url=url, verify=False, **kwargs))


def get(url, params=None, **kwargs):
    return __judge_code(__s.get(url=url, params=params, verify=False, **kwargs))


def post(url, data=None, json=None, **kwargs):
    return __judge_code(__s.post(url=url, data=data, json=json, verify=False, **kwargs))
