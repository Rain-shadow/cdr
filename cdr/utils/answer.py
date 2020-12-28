#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-19, 0019 19:51
# @Author: 佚名
# @File  : answer.py
import re
from .course import Course
from .log import Log
from .set import Set
from .adapt import adapter
from cdr.exception import AnswerNotFoundException


class Answer:

    def __init__(self, course: Course):
        self._course = course

    # assist_word 时态不确定的单词
    # remark 例句的翻译
    # options 题目选项
    def find_answer_by_11(self, assist_word: str, remark: str, options: list) -> str:
        Log.d("\nfind_answer_by_11")
        Log.d(assist_word)
        Log.d(options)
        # 根据辅助词先行过滤出一个粗略的可能性列表
        answer_list = self._course.find_detail_by_assist_word(assist_word)
        Log.d(answer_list)
        if len(answer_list) == 0:
            # 辅助词过滤出现未适配情况或者出现答案预处理出错的情况
            raise AnswerNotFoundException(11)
        for answer in answer_list:
            for content in answer["content"]:
                if content["example"].get(remark) or adapter.example_get_remark(content["example"], remark):
                    Log.d(content["example"][remark])
                    for mean in options:
                        tem_list = [mean["content"]]
                        tem_list.extend(adapter.process_option_mean(mean["content"]))
                        # 若选项集合与题库集合的交集存在，则说明该选项等于题库中的某个选项
                        # 由 mean == content["mean"] 拓展适配得来
                        if len(Set(tem_list) & Set(adapter.process_word_mean(content["mean"]))) != 0:
                            return str(mean["answer_tag"])
        raise AnswerNotFoundException(11)

    # assist_word 时态不确定的单词
    # remark 例句的翻译
    # options 题目选项
    def find_answer_by_13(self, assist_word: str, remark: str, options: list) -> str:
        Log.d("\nfind_answer_by_13")
        Log.d(assist_word)
        Log.d(options)
        answer_list = self._course.find_detail_by_assist_word(assist_word)
        Log.d(answer_list)
        if len(answer_list) == 0:
            raise AnswerNotFoundException(13)
        for answer in answer_list:
            for content in answer["content"]:
                if content["example"].get(remark) or adapter.example_get_remark(content["example"], remark):
                    #   创建一个临时列表，方便下一步判断答案
                    tem_list = []
                    for key in content["example"]:
                        if key != remark:   # 本题是根据题目例句选择与例句同列的例句，故需排除题目例句本身
                            tem_list.append(content["example"][key])
                    for sentence in options:
                        if sentence["content"] in tem_list:
                            Log.d(sentence["content"])
                            return str(sentence["answer_tag"])
        raise AnswerNotFoundException(13)

    # 16、21、22与其处理方式一致
    # word 单词原型，精确匹配，效率极高
    # options 题目选项
    def find_answer_by_15(self, word: str, options: list) -> str:
        Log.d("\nfind_answer_by_15")
        Log.d(word)
        Log.d(options)
        answer = self._course.find_detail_by_word(word)
        Log.d(answer)
        if answer is None:
            raise AnswerNotFoundException(15)
        #   创建一个临时列表
        tem_list = []
        for content in answer["content"]:
            tem_list.append(content["mean"])
            tem_list.extend(adapter.process_word_mean(content["mean"]))
        for mean in options:
            if len(Set(tem_list) & Set(adapter.process_option_mean(mean["content"]))) != 0:
                return str(mean["answer_tag"])
        raise AnswerNotFoundException(15)

    # 18与其处理方式一致
    # content 单词词义
    # options 题目选项
    def find_answer_by_17(self, content: str, options: list) -> str:
        Log.d("\nfind_answer_by_17")
        Log.d(content)
        content = re.sub(r'\s\s', ' ', content)
        Log.d(content)
        Log.d(options)
        for word in options:
            answer = self._course.find_detail_by_word(word["content"])
            Log.d(answer)
            if answer is None:  # 选项中可能存在不在课程中的单词，故查询结果可能为空
                continue
            #   创建一个临时列表
            tem_list = []
            for mean in answer["content"]:
                tem_list.append(mean["mean"])
                tem_list.extend(adapter.process_word_mean(mean["mean"]))
            if len(Set(tem_list) & Set(adapter.process_word_mean(content))) != 0:
                return str(word["answer_tag"])
        raise AnswerNotFoundException(17)

    # 无需兼容，本身即可得出答案，最让人安心的一个
    @staticmethod
    def find_answer_by_31(remark: list, options: list) -> list:
        Log.d("\find_answer_by_31")
        Log.d(options)
        tem_list = []
        for i in remark:
            tem_list.append(i["relation"])
        result = []
        for i in options:
            if i["content"] in tem_list:
                result.append(str(i["answer_tag"]))
        return result

    # remark 单词的短语翻译
    # options 题目选项
    # blank_count 填空所需单词数量
    def find_answer_by_32(self, remark: str, options: list, blank_count: int) -> str:
        Log.d("\nfind_answer_by_32")
        Log.d(options)
        Log.d(f"{blank_count:d}")
        # 选项预处理
        option_list = []  # 存放选项中的短语，短语由规定顺序的单词数组构成
        for usage in options:
            option_list.extend(re.split(r"\s+", usage["content"].strip()))
        Log.d(option_list, is_show=False)
        option_set = Set(option_list)

        for value in self._course.data.values():
            for content in value["content"]:
                usage_list = content["usage"].get(remark) or adapter.usage_get_remark(content["usage"], remark)
                if usage_list is not None:
                    Log.d(usage_list, is_show=False)
                    for usage in usage_list:
                        if len(option_set & Set(usage)) == len(usage):
                            if len(usage) == blank_count:
                                return ",".join(usage)
                            # 下列情况为一个选项中存在多个单词（说好的一个单词一个选项呢？？？）
                            result = adapter.answer_32(options, usage)
                            if result:
                                return result
        raise AnswerNotFoundException(32)

    # 42与其处理方式一致
    # content 英语例句
    # remark 例句的翻译
    # options 题目选项
    def find_answer_by_41(self, content: str, remark: str, options: list) -> str:
        Log.d("\nfind_answer_by_41")
        Log.d(content)
        content = adapter.process_option_sentence(content)  # 合着您传输多个空格就为了增加网页端单词间距显示？？？
        Log.d(content)
        Log.d(options)
        for word in options:
            answer_list = self._course.find_detail_by_assist_word(word["content"])
            if len(answer_list) == 0:
                continue
            for answer in answer_list:
                Log.d(answer)
                if answer is not None:
                    for example in answer["content"]:
                        for key in example["example"]:
                            # 例句翻译相同的情况下，可能出现多个单词用到了同一个例句
                            if remark == key and content.find("{") == example["example"][key].find("{"):
                                return str(word["answer_tag"])
        raise AnswerNotFoundException(41)

    # 44与其处理方式一致
    # content 英语例句
    # remark 例句的翻译
    # options 题目选项
    def find_answer_by_43(self, content, remark, options) -> str:
        Log.d("\nfind_answer_by_43")
        Log.d(content)
        content = adapter.process_option_sentence(content)  # 合着您传输多个空格就为了增加网页端单词间距显示？？？
        Log.d(content)
        Log.d(options)
        for option in options:
            answer = self._course.find_detail_by_word(option["content"])
            if answer is None:
                continue
            Log.d(answer)
            if answer is not None:
                #   创建一个临时列表，存放例句翻译
                tem_list = []
                for example in answer["content"]:
                    for key in example["example"]:
                        tem_list.append(key)
                if remark in tem_list:
                    if option["sub_options"] is not None:
                        assist_word = None
                        position = -2
                        for example in answer["content"]:
                            if example["example"].get(remark) is not None:
                                tem_content = example["example"][remark]
                                assist_word = tem_content[tem_content.find("{") + 1:tem_content.find("}")]
                                position = tem_content.find("{")
                                break
                        for sub in option["sub_options"]:
                            if sub["content"] == assist_word and content.find("{") == position:
                                return option["answer_tag"] + str(sub["answer_tag"])
                    else:
                        return option["answer_tag"] + "0"
        raise AnswerNotFoundException(43)

    # 52与其处理方式一致
    # content 带{}的短语
    # remark 短语翻译
    def find_answer_by_51(self, content: str, remark: str) -> str:
        Log.d("\nfind_answer_by_51")
        Log.d(content)
        Log.d(remark)
        usage_list = adapter.process_option_usage(content).split(" ")
        usage_list_set = Set(usage_list)
        Log.d(usage_list)
        #   被弃用的正则表达式：
        #   (?:noun|verb|prep|adj|adv|conj|pron|excl|PRON-POSS|QUANT)\s?(.*)
        pattern = re.compile(r"(?:[A-Za-z-]*)?\s?(.*)")
        for key, value in self._course.data.items():
            if len(usage_list) == 1:
                for i in value["content"]:
                    matcher = pattern.match(i["mean"])
                    if remark == matcher.group(1):
                        return key
            else:
                for content in value["content"]:
                    usages = content["usage"].get(remark) or adapter.usage_get_remark(content["usage"], remark)
                    if usages is not None:
                        for usage in usages:
                            if len(usage_list) - 1 != len(usage_list_set & Set(usage)):
                                continue
                            for index, word in enumerate(usage):
                                if word != usage_list[index]:
                                    # 原本只需返回usage[index]即可
                                    # 但因兼容CET4_3的at one's {}'s end(智穷力竭)特殊案例，不得不复杂化
                                    return adapter.answer_51(usage_list[index], usage[index])
        raise AnswerNotFoundException(51)

    # 54与其处理方式一致
    # content 英语例句
    # remark 例句翻译
    def find_answer_by_53(self, content: str, remark: str) -> str:
        Log.d("\nfind_answer_by_53")
        Log.d(content)
        Log.d(remark)
        content = adapter.process_option_sentence(content)
        Log.d(content)
        for key, value in self._course.data.items():
            for example in value["content"]:
                if content == "{}":
                    # 由 example["mean"] == remark 拓展适配得来
                    # 感谢群友148***020提供的错误日志，263-269行代码由其帮助得来
                    if len(Set(adapter.process_word_mean(example["mean"]))
                           & Set(adapter.process_option_mean(remark))) != 0:
                        return key
                else:
                    if example["example"].get(remark) is not None:
                        sentence = example["example"][remark]
                        #   不同单词可能具有相同例句，因测试其第一个"{"的位置是否相等
                        if content.find("{") == sentence.find("{"):
                            return sentence[sentence.find("{") + 1:sentence.find("}")]
        raise AnswerNotFoundException(53)
