#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-30, 0030 16:09
# @Author: 佚名
# @File  : requests.py
import requests
from cdr.exception import NetworkError
__s = requests.Session()
__s.adapters.DEFAULT_RETRIES = 5
__s.keep_alive = False


def __judge_code(res: requests.models.Response) -> requests.models.Response:
    if res.status_code != 200:
        raise NetworkError(res.status_code, res.content.decode("utf-8"))
    return res


def options(url, **kwargs):
    return __judge_code(__s.options(url=url, **kwargs))


def get(url, params=None, **kwargs):
    return __judge_code(__s.get(url=url, params=params, **kwargs))


def post(url, data=None, json=None, **kwargs):
    return __judge_code(__s.post(url=url, data=data, json=json, **kwargs))

