#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-23, 0023 17:52
# @Author: 佚名
# @File  : answer_adapter.py
import inspect
import sys
import re
from .interface import IOrigin

_interfaces = []

for __cls_name, __cls in inspect.getmembers(sys.modules["cdr.utils.adapt.interface"], inspect.isclass):
    if re.match(r"^AnswerPattern[1-9]\d*$", __cls_name):
        _interfaces.append(__cls)


# TODO
class AnswerAdapter:

    def __init__(self):
        self.__interfaces = _interfaces

    # 无则原样返回
    def process_content_and_remark(self, content: str, remark: str) -> (str, str):
        for cls in self.__interfaces:
            content, remark = cls.process_content_and_remark(content, remark)
        return content, remark

    # 无则返回None
    def example_get_remark(self, example_list: dict, remark: str) -> str:
        for cls in self.__interfaces:
            result = cls.example_get_remark(example_list, remark)
            if result:
                return result

    # 无则返回None
    def usage_get_remark(self, usage_list: dict, remark: str) -> list:
        for cls in self.__interfaces:
            result = cls.usage_get_remark(usage_list, remark)
            if result:
                return result

    # 无则返回[]
    def process_option_mean(self, mean: str) -> list:
        # 21.3.17修复由群友253***349提交的BUG
        # 该BUG让我注意到设计适配器之初忘记将原本的翻译添加进列表中
        result = [mean]
        for cls in self.__interfaces:
            result.extend(cls.process_option_mean(mean))
        return result

    # 无则返回[]
    def process_word_mean(self, mean: str) -> list:
        result = [mean]
        for cls in self.__interfaces:
            result.extend(cls.process_word_mean(mean))
        return result

    # 无则返回sentence
    def process_option_sentence(self, sentence: str) -> str:
        for cls in self.__interfaces:
            result = cls.process_option_sentence(sentence)
            if result and result != sentence:
                return result
        return sentence

    # 无则返回usage
    def process_option_usage(self, usage: str) -> str:
        result = usage
        for cls in self.__interfaces:
            result = cls.process_option_usage(result)
        return result

    # 无则返回None
    def answer_32_1(self, options: list, usage: list) -> str:
        for cls in self.__interfaces:
            result = cls.answer_32_1(options, usage)
            if result:
                return result

    # 无则返回None
    def answer_32_2(self, options: list, usage: list) -> str:
        for cls in self.__interfaces:
            result = cls.answer_32_2(options, usage)
            if result:
                return result

    # 无则返回word
    def answer_51(self, option_word: str, word: str) -> str:
        for cls in self.__interfaces:
            result = cls.answer_51(option_word, word)
            if result:
                return result
        return word
