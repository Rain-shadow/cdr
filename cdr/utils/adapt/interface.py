#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-23, 0023 17:53
# @Author: 佚名
# @File  : interface.py
import re
from ..tool import Tool


# 接口基类
class IOrigin:

    # 处理不同情况下的翻译以从例句列表中得到对应的英语例句
    @staticmethod
    def example_get_remark(example_list: dict, remark: str) -> str:
        pass

    # 处理不同情况下的翻译以从短语列表中得到对应的英语短语数组
    @staticmethod
    def usage_get_remark(usage_list: dict, remark: str) -> list:
        pass

    # 处理选项中单词词义
    @staticmethod
    def process_option_mean(mean: str) -> list:
        pass

    # 处理题库中单词词义
    @staticmethod
    def process_word_mean(mean: str) -> list:
        pass

    @staticmethod
    def process_option_sentence(sentence: str) -> str:
        pass

    @staticmethod
    def process_option_usage(usage: str) -> str:
        pass

    @staticmethod
    def answer_32(options: list, usage: list) -> str:
        pass

    @staticmethod
    def answer_51(option_word: str, word: str) -> str:
        return word


# 代码重构适配
class AnswerPattern1(IOrigin):

    @staticmethod
    def usage_get_remark(usage_list: dict, remark: str) -> list:
        tem = remark.replace('.', ' ').replace("…", " ").replace("-", " ").replace(",", " ")
        # 处理因清理"..."而造成的多余空格
        tem = " ".join(tem.split())
        return usage_list.get(tem)

    @staticmethod
    def process_option_mean(mean: str) -> list:
        return [Tool.sort_str(mean), mean + "；", Tool.sort_str(mean + "；")]

    @staticmethod
    def process_word_mean(mean: str) -> list:
        return [Tool.sort_str(mean)]

    @staticmethod
    def process_option_sentence(sentence: str) -> str:
        return re.sub(r'\s\s', ' ', sentence)

    @staticmethod
    def process_option_usage(usage: str) -> str:
        tem = usage.replace('.', ' ').replace("…", " ").replace("-", " ").replace(",", " ")
        return " ".join(tem.split())

    @staticmethod
    def answer_32(options: list, usage: list) -> str:
        result = []
        tem_map = {}
        for index, option in enumerate(options):
            for tem_value in re.split(r"\s+", option["content"].strip()):
                tem_map[tem_value] = index
        for word in usage:
            if len(result) == 0 or tem_map[result[len(result) - 1]] != tem_map.get(word):
                result.append(word)
            else:
                result[len(result) - 1] = options[tem_map[word]]["content"]
        return ",".join(result)

    @staticmethod
    def answer_51(option_word: str, word: str) -> str:
        return word.replace(option_word.replace("{", "").replace("}", ""), "")


# 20.12.29修复由群友183***092提交的BUG
# 处理选项中莫名其妙多出来的一个"，"
class AnswerPattern2(IOrigin):

    @staticmethod
    def process_word_mean(mean: str) -> list:
        tem = mean.replace("，", "").replace(" ", "")
        return [tem, Tool.sort_str(tem)]

    @staticmethod
    def process_option_mean(mean: str) -> list:
        tem = mean.replace("，", "").replace(" ", "")
        return [tem, Tool.sort_str(tem)]
