#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-30, 0030 16:09
# @Author: 佚名
# @File  : request.py
from json import JSONDecodeError

import requests
import urllib3
from requests.adapters import HTTPAdapter

from cdr.utils import Log
from .network_error import NetworkError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__s = requests.Session()
__s.mount('http://', HTTPAdapter(max_retries=15))
__s.mount('https://', HTTPAdapter(max_retries=15))
__s.adapters.DEFAULT_RETRIES = 15
__s.keep_alive = False


def __judge_code(res: requests.models.Response) -> requests.models.Response:
    Log.i(res.content.decode("utf-8"), is_show=False)
    if res.status_code != 200:
        if res.url != "https://app.vocabgo.com/student/":
            raise NetworkError(res.status_code, res.url, res.content.decode("utf-8"))
    else:
        try:
            json_data = res.json()
        except JSONDecodeError:
            pass
        else:
            if json_data and (json_data["code"] == 0 or json_data["code"] == 10002):
                Log.e(f"{json_data['code']}, {res.url}, {json_data['msg']}", is_show=False)
    return res


def options(url, **kwargs):
    return __judge_code(__s.options(url=url, verify=False, **kwargs))


def get(url, params=None, **kwargs):
    return __judge_code(__s.get(url=url, params=params, verify=False, **kwargs))


def post(url, data=None, json=None, **kwargs):
    return __judge_code(__s.post(url=url, data=data, json=json, verify=False, **kwargs))

