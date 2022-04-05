#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-23, 0023 17:52
# @Author: 佚名
# @File  : answer_adapter.py
import inspect
import sys
import re
from .. import Set

_interfaces = []

for __cls_name, __cls in inspect.getmembers(sys.modules["cdr.utils.adapt.interface"], inspect.isclass):
    if re.match(r"^AnswerPattern[1-9]\d*$", __cls_name):
        _interfaces.append(__cls)


class AnswerAdapter:

    def __init__(self):
        self.__interfaces = _interfaces

    # 无则原样返回
    def process_content_and_remark(self, content: str, remark: str):
        for cls in self.__interfaces:
            content, remark = cls.process_content_and_remark(content, remark)
        return content, remark

    # 无则返回False
    def is_remark_or_sentence_in_example(self, example_dict: dict, remark: str, sentence: str) -> bool:
        for cls in self.__interfaces:
            result = cls.is_remark_or_sentence_in_example(example_dict, remark, sentence)
            if result:
                return result
        return False

    # 无则返回None
    def phrase_get_remark(self, phrase_dict: dict, remark: str) -> list:
        for cls in self.__interfaces:
            result = cls.phrase_get_remark(phrase_dict, remark)
            if result:
                return result

    def phrase_get_remark_by_ratio(self, phrase_dict: dict, remark_list: list, ratio: float = 0.6) -> list:
        for cls in self.__interfaces:
            result = cls.phrase_get_remark_by_ratio(phrase_dict, remark_list, ratio, self)
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

    # 无则返回phrase
    def process_option_phrase(self, phrase: str) -> str:
        result = phrase
        for cls in self.__interfaces:
            result = cls.process_option_phrase(result)
        return result

    # 无则返回[phrase]
    def process_answer_phrase(self, phrase: list[str]) -> list[list[str]]:
        result = [phrase]
        for cls in self.__interfaces:
            tem = cls.process_answer_phrase(phrase)
            if tem is not None:
                result.append(tem)
        return result


    # 无则返回None
    def answer_11_1(self, remark: str, skip_times: int, options: list, answer_list: list) -> str:
        for cls in self.__interfaces:
            result = cls.answer_11_1(remark, skip_times, options, answer_list, self)
            if result:
                return result

    # 无则返回None
    def answer_11_2(self, sentence: str, remark: str, skip_times: int,
                    options: list, answer_list: list) -> str:
        for cls in self.__interfaces:
            result = cls.answer_11_2(sentence, remark, skip_times, options, answer_list, self)
            if result:
                return result

    # 无则返回None
    def answer_15_1(self, answer_list: list, options: list) -> str:
        for cls in self.__interfaces:
            result = cls.answer_15_1(answer_list, options, self)
            if result:
                return result

    # 无则返回None
    def answer_15_2(self, answer_list: list, options: list) -> str:
        result = None
        for cls in self.__interfaces:
            result_tuple = cls.answer_15_2(answer_list, options, self)
            if result is None:
                result = result_tuple
            elif result_tuple and result[1] <= result_tuple[1]:
                result = result_tuple
        if result is not None:
            return result[0]

    # 无则返回None
    def answer_17_1(self, content_list: list, options: list, answer_list: list) -> str:
        for cls in self.__interfaces:
            result = cls.answer_17_1(content_list, options, answer_list, self)
            if result:
                return result

    # 无则返回None
    def answer_32_1(self, options: list, phrase: list) -> str:
        for cls in self.__interfaces:
            result = cls.answer_32_1(options, phrase)
            if result:
                return result

    # 无则返回None
    def answer_32_2(self, options: list, phrase: list) -> str:
        for cls in self.__interfaces:
            result = cls.answer_32_2(options, phrase)
            if result:
                return result

    # 无则返回None
    def answer_32_3(self, options: list, phrase_list: list[list], blank_count: int, skip_times: int) -> str:
        for cls in self.__interfaces:
            result = cls.answer_32_3(options, phrase_list, blank_count, skip_times, self)
            if result:
                return result

    # 无则返回None
    def answer_32_4(self, content: str, remark: str, options: list, blank_count: int, skip_times: int, answer_dict: dict) -> str:
        for cls in self.__interfaces:
            result = cls.answer_32_4(content, remark, options, blank_count, skip_times, answer_dict, self)
            if result:
                return result

    # 无则返回word
    def answer_51(self, option_word: str, word: str) -> str:
        for cls in self.__interfaces:
            result = cls.answer_51(option_word, word)
            if result:
                return result
        return word

    # 无则返回None
    def answer_51_1(self, answer: dict, remark: str, skip_times: int, phrase_list: list, phrase_list_set: Set) -> str:
        for cls in self.__interfaces:
            result = cls.answer_51_1(answer, remark, skip_times, phrase_list, phrase_list_set, self)
            if result:
                return result

    # 无则返回None
    def answer_51_2(self, answer: dict, remark: str, skip_times: int, phrase_list: list, phrase_list_set: Set) -> str:
        for cls in self.__interfaces:
            result = cls.answer_51_2(answer, remark, skip_times, phrase_list, phrase_list_set, self)
            if result:
                return result
