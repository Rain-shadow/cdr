#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-19, 0019 23:08
# @Author: 佚名
# @File  : excepthook.py
import asyncio
import threading
import sys
from requests import ReadTimeout
from requests.exceptions import ProxyError, ConnectionError
from aiohttp.client_exceptions import ServerDisconnectedError, ClientConnectorError, ClientOSError
from urllib3.exceptions import NewConnectionError, MaxRetryError

from cdr.aio import aiorequset
from cdr.request.network_error import NetworkError
from cdr.request.upper_limit_error import UpperLimitError
from cdr.utils.log import Log
from cdr.config import LOG_DIR_PATH

_logger = Log.get_logger()


def __my_except_hook(exc_type, exc_value, tb):
    msg = ' Traceback (most recent call last):\n'
    while tb:
        filename = tb.tb_frame.f_code.co_filename
        name = tb.tb_frame.f_code.co_name
        lineno = tb.tb_lineno
        msg += '   File "%.500s", line %d, in %.500s\n' % (filename, lineno, name)
        tb = tb.tb_next

    msg += ' %s: %s\n' % (exc_type.__name__, exc_value)

    _logger.v("")
    _logger.e(msg, is_show=False)
    aiorequset.close_session()
    network_error = (ReadTimeout, ConnectionError, NewConnectionError, MaxRetryError,
                     ServerDisconnectedError, ClientConnectorError)
    if exc_type == ValueError and str(exc_value) == "check_hostname requires server_hostname" \
            or isinstance(exc_value, ProxyError):
        _logger.e("该软件无法在全局代理开启的情况下运行！")
    elif isinstance(exc_value, network_error):
        _logger.e(exc_value)
        _logger.e("网络不稳定，请待网络恢复后重启程序")
    elif exc_type == KeyboardInterrupt:
        _logger.v("")
        _logger.i("AWSL")
    elif exc_type == NetworkError:
        _logger.e(f"词达人自己崩了！\n{exc_value.msg}")
        _logger.create_error_txt()
    elif exc_type == SystemExit:
        pass
    elif exc_type == UpperLimitError:
        _logger.w(f"\n{exc_type}", is_show=False)
        _logger.w(f"\n{exc_value.msg}")
        _logger.w("注：该限制为词达人官方行为，与作者无关\n按回车退出程序")
        input()
        sys.exit(0)
    elif exc_type == ClientOSError:
        _logger.e(exc_value)
        _logger.e("作者语：不清楚·不知道·别问我")
        input("按回车键退出程序")
        sys.exit(0)
    else:
        _logger.e(exc_value)
        _logger.e("未知异常，请上报此错误（error-last.txt）给GM")
        _logger.e(f"你可以在“main{LOG_DIR_PATH[1:]}”下找到error-last.txt")
        _logger.create_error_txt()
    if threading.current_thread() is threading.main_thread():
        _logger.close_all_logger()
        input("按回车键退出程序")
        sys.exit(1)


def handle_async_exception(loop, context):
    # first, handle with default handler
    exception = context.get('exception')
    if exception is not None:
        __my_except_hook(type(exception), exception, exception.__traceback__)
    # loop.default_exception_handler(context)
    loop.stop()


def hook_except():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_async_exception)
    sys.excepthook = __my_except_hook
