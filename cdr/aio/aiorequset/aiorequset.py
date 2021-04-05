#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-30, 0030 16:09
# @Author: 佚名
# @File  : aiorequest.py
from json import JSONDecodeError

import asyncio
import aiohttp
import urllib3

from cdr.utils import Log
from cdr.request.network_error import NetworkError
from cdr.request.upper_limit_error import UpperLimitError

__s = aiohttp.ClientSession()
_logger = Log.get_logger()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


async def __judge_code(res: aiohttp.ClientResponse) -> aiohttp.ClientResponse:
    _logger.i(await res.text(), is_show=False)
    if res.status != 200:
        if res.url != "https://app.vocabgo.com/student/":
            raise NetworkError(res.status, res.url, await res.text("utf-8"))
    else:
        try:
            json_data = await res.json()
        except JSONDecodeError:
            pass
        else:
            if res.url.raw_path.find("gateway.vocabgo.com") != -1:
                if json_data and (json_data["code"] == 0 or json_data["code"] == 10002
                                  or json_data["code"] == 21006):
                    _logger.e(f"{json_data['code']}, {res.url}, {json_data['msg']}", is_show=False)
                if json_data and json_data["code"] == 10017:
                    raise UpperLimitError(res.status, res.url, json_data["msg"])
    return res


async def options(url, **kwargs) -> aiohttp.ClientResponse:
    async with __s.options(url, **kwargs) as res:
        return res


async def get(url, params=None, **kwargs) -> aiohttp.ClientResponse:
    async with __s.get(url=url, params=params, **kwargs) as res:
        return await __judge_code(res)


async def post(url, data=None, json=None, **kwargs) -> aiohttp.ClientResponse:
    async with __s.post(url=url, data=data, json=json, **kwargs) as res:
        return await __judge_code(res)


def close_session():
    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(__s.close(), loop)
