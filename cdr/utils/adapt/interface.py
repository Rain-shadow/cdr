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
        return []

    # 处理题库中单词词义
    @staticmethod
    def process_word_mean(mean: str) -> list:
        return []

    # 处理选项中英语例句的特殊情况（目前只是遇见多空格）
    @staticmethod
    def process_option_sentence(sentence: str) -> str:
        pass

    # 处理选项中短语翻译的特殊情况（如多出莫名其妙的符号）
    @staticmethod
    def process_option_usage(usage: str) -> str:
        pass

    # 处理题型32中一个选项中包含多个单词的情况
    @staticmethod
    def answer_32_1(options: list, usage: list) -> str:
        pass

    # 处理题型32中选项中包含奇怪的情况
    @staticmethod
    def answer_32_2(options: list, usage: list) -> str:
        """
        :param options: 原选项
        :param usage: 已经匹配出来的短语
        :return: 合成好的答案
        """
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
        #去汉字
        re.sub(r"[\u4E00-\u9FA5]", "", usage)
        #去除ZZ的图标字符串
        tem = re.sub(r"\\[uU][eE][0-9a-fA-F]{3}", "", usage.encode('unicode-escape').decode("utf-8"))\
            .encode('utf-8').decode("unicode-escape")
        tem = tem.replace('.', ' ').replace("…", " ").replace("-", " ").replace(",", " ").replace("\n", "").strip()
        return " ".join(tem.split())

    @staticmethod
    def answer_32_1(options: list, usage: list) -> str:
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
    def answer_32_2(options: list, usage: list) -> str:
        for index, value in enumerate(usage):
            for v in options:
                if value == AnswerPattern1.process_option_usage(v["content"]):
                    usage[index] = v["content"]
        return ",".join(usage)

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


# 20.12.29修复由群友253***814提交的BUG
# 这是他在看着电视没事干时试出来的
# 处理选项中括号及括号中的内容
class AnswerPattern3(IOrigin):

    @staticmethod
    def process_option_mean(mean: str) -> list:
        # 去除多余的<>
        tem = re.sub(r"[<(（].*?[）)>]", "", mean)
        return [tem, Tool.sort_str(tem)]
