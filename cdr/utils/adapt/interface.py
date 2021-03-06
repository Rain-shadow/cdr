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

    # 处理传入的content, remark混合问题
    @staticmethod
    def process_content_and_remark(content: str, remark: str):
        return content, remark

    # 处理不同情况下的翻译以从例句列表中得到对应的英语例句
    @staticmethod
    def is_remark_or_sentence_in_example(example_dict: dict, remark: str, sentence: str) -> bool:
        return example_dict.get(remark) is not None

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
        return usage

    # 处理题型11中精确匹配失败的情况
    # 为例句翻译添加模糊匹配
    @staticmethod
    def answer_11_1(remark: str, skip_times: int, options: list, answer_list: list, adapter) -> str:
        pass

    # 处理题型11中精确匹配失败的情况
    # 为选项翻译添加模糊匹配
    @staticmethod
    def answer_11_2(sentence: str, remark: str, skip_times: int, options: list, answer_list: list, adapter) -> str:
        pass

    # 处理题型15中精确匹配失败的情况
    # 为选项翻译添加模糊匹配
    @staticmethod
    def answer_15_1(answer_list: list, options: list, adapter) -> str:
        pass

    # 处理题型17中精确匹配失败的情况
    # 为选项翻译添加模糊匹配
    @staticmethod
    def answer_17_1(content_list: list, options: list, answer_dict: dict, adapter) -> str:
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
    def process_content_and_remark(content: str, remark: str):
        # 21.3.17修复由群友转交给115***706提交的BUG，我们仍未知道那天是哪位群友的贡献
        # 这个就离谱了，把remark内容放到content中可还行？？？
        if remark is None and content.find("\n") != -1:
            tem_list = content.split("\n")
            content = tem_list[0]
            remark = tem_list[1]
        return content, remark

    @staticmethod
    def is_remark_or_sentence_in_example(example_dict: dict, remark: str, sentence: str) -> bool:
        sentence = " ".join(sentence.split())
        for value in example_dict.values():
            if value == sentence:
                return True
        for key in example_dict.keys():
            if Tool.get_ratio_between_str(key, remark) >= 0.9:
                return True
        return False

    @staticmethod
    def usage_get_remark(usage_list: dict, remark: str) -> list:
        tem = remark.replace('.', ' ').replace("…", " ").replace("-", " ").replace(",", " ")
        # 处理因清理"..."而造成的多余空格
        tem = " ".join(tem.split())
        return usage_list.get(tem) or usage_list.get(remark.replace("…", "", 1).strip())

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
        # 去汉字
        re.sub(r"[\u4E00-\u9FA5]", "", usage)
        # 去除ZZ的图标字符串
        tem = re.sub(r"\\[uU][eE][0-9a-fA-F]{3}", "", usage.encode('unicode-escape').decode("utf-8"))\
            .encode('utf-8').decode("unicode-escape")
        tem = tem.replace('.', ' ').replace("…", " ").replace("-", " ").replace(",", " ").replace("\n", "").strip()
        return " ".join(tem.split())

    # 模糊匹配
    @staticmethod
    def answer_11_1(remark: str, skip_times: int, options: list, answer_list: list, adapter) -> str:
        for answer in answer_list:
            for content in answer["content"]:
                for key in content["example"].keys():
                    if Tool.get_ratio_between_str(key, remark) < 0.75:
                        continue
                    for mean in options:
                        tem_list = adapter.process_option_mean(mean["content"])
                        # 若选项集合与题库集合的相似度超过3/4，则该选项有可能等于题库中的选项
                        if len(set(tem_list) & set(adapter.process_word_mean(content["mean"]))) != 0:
                            if skip_times != 0:
                                skip_times -= 1
                                continue
                            return str(mean["answer_tag"])

    @staticmethod
    def answer_11_2(sentence: str, remark: str, skip_times: int, options: list, answer_list: list, adapter) -> str:
        lowest_ratio = 0.7  # 若选项集合与题库集合的相似度超过3/4，则该选项有可能等于题库中的选项
        if len(answer_list) == 1:   # 若题库集合仅1个，降低匹配率，仅需确保不会匹配到非
            lowest_ratio = 0.5
        for answer in answer_list:
            for content in answer["content"]:
                if adapter.is_remark_or_sentence_in_example(content["example"], remark, sentence):
                    for mean in options:
                        tem_list = adapter.process_option_mean(mean["content"])
                        if Tool.get_ratio_between_list(tem_list,
                                                       adapter.process_word_mean(content["mean"])) >= lowest_ratio:
                            if skip_times != 0:
                                skip_times -= 1
                                continue
                            return str(mean["answer_tag"])

    @staticmethod
    def answer_15_1(answer_list: list, options: list, adapter) -> str:
        for mean in options:
            if Tool.get_ratio_between_list(
                    adapter.process_option_mean(mean["content"]), answer_list) >= 0.8:
                return str(mean["answer_tag"])

    @staticmethod
    def answer_17_1(content_list: list, options: list, answer_dict: dict, adapter) -> str:
        for word in options:
            answer = answer_dict.get(word["content"])
            if answer is None:  # 选项中可能存在不在课程中的单词，故查询结果可能为空
                continue
            #   创建一个临时列表
            tem_list = []
            for mean in answer["content"]:
                tem_list.extend(adapter.process_word_mean(mean["mean"]))
            if Tool.get_ratio_between_list(tem_list, content_list) >= 0.8:
                return str(word["answer_tag"])

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


# 21.3.17修复由群友253***349提交的BUG
# 处理填空时根据单词翻译填单词，翻译中多出单词类型的问题
class AnswerPattern4(IOrigin):

    @staticmethod
    def process_word_mean(mean: str) -> list:
        return [re.sub(r"(?:[A-Za-z-]*)?\s?", "", mean)]


# 21.3.23修复由群友839***272提交的BUG
# 处理短语翻译多出符号问题
class AnswerPattern5(IOrigin):

    @staticmethod
    def usage_get_remark(usage_list: dict, remark: str) -> list:
        is_more = re.compile(r"(.*…)\s(…[^a-zA-Z]*)")
        if is_more.match(remark) is None:
            matcher = re.match(r"([0-9A-Za-z.\s(){}'/&‘’,（）…-]*)?\s(.*)", remark)
        else:
            matcher = re.match(r"([0-9A-Za-z.\s(){}'/&‘’,（）…-]*)?\s(….*)", remark)
        if matcher is None:
            return None
        return usage_list.get(matcher.group(2).strip())


# 21.3.25修复由群友224***087提交的BUG
# 这是他在看着电视没事干时试出来的
# 处理选项中多余的中文括号
class AnswerPattern6(IOrigin):

    @staticmethod
    def process_option_mean(mean: str) -> list:
        # 去除多余的中文括号
        tem = re.sub(r"([A-Za-z\s]+)?(（?(?:(?!（).)+）)", r"\1", mean)
        return [tem, Tool.sort_str(tem)]


# 21.4.17修复由群友148***020提交的BUG
# 处理多余空格并乱序
class AnswerPattern7(IOrigin):

    @staticmethod
    def process_option_mean(mean: str) -> list:
        # 移除所有空格并排序
        return [Tool.sort_str(re.sub(r"\s+", "", mean))]

    @staticmethod
    def process_word_mean(mean: str) -> list:
        # 移除所有空格并排序
        return [Tool.sort_str(re.sub(r"\s+", "", mean))]
