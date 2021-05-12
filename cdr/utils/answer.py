#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-19, 0019 19:51
# @Author: 佚名
# @File  : answer.py
import re
from .course import Course
from .log import Log
from .set import Set
from .tool import Tool
from .adapt import adapter
from cdr.exception import AnswerNotFoundException

_logger = Log.get_logger()


class Answer:

    def __init__(self, course: Course):
        self._course = course

    # assist_word 时态不确定的单词
    # remark 例句的翻译
    # options 题目选项
    def find_answer_by_11(self, sentence: str, remark: str, options: list, skip_times: int) -> str:
        _logger.d("\nfind_answer_by_11")
        _logger.d(sentence)
        assist_word = sentence[sentence.find("{") + 1:sentence.find("}")].strip()
        _logger.d(assist_word)
        _logger.d(options)
        # 根据辅助词先行过滤出一个粗略的可能性列表
        answer_list = self._course.find_detail_by_assist_word(assist_word)
        _logger.d(answer_list)
        if len(answer_list) == 0:
            # 辅助词过滤出现未适配情况或者出现答案预处理出错的情况
            raise AnswerNotFoundException(11)
        for answer in answer_list:
            for content in answer["content"]:
                if adapter.is_remark_or_sentence_in_example(content["example"], remark, sentence):
                    for mean in options:
                        tem_list = adapter.process_option_mean(mean["content"])
                        # 若选项集合与题库集合的交集存在，则说明该选项等于题库中的某个选项
                        # 由 mean == content["mean"] 拓展适配得来
                        if len(set(tem_list) & set(adapter.process_word_mean(content["mean"]))) != 0:
                            if skip_times != 0:
                                skip_times -= 1
                                continue
                            return str(mean["answer_tag"])
        vague_answer = adapter.answer_11_1(remark, skip_times, options, answer_list)
        if vague_answer:
            return vague_answer
        vague_answer = adapter.answer_11_2(sentence, remark, skip_times, options, answer_list)
        if vague_answer:
            return vague_answer
        raise AnswerNotFoundException(11)

    # assist_word 时态不确定的单词
    # remark 例句的翻译
    # options 题目选项
    def find_answer_by_13(self, sentence: str, remark: str, options: list) -> str:
        _logger.d("\nfind_answer_by_13")
        _logger.d(sentence)
        assist_word = sentence[sentence.find("{") + 1:sentence.find("}")].strip()
        _logger.d(assist_word)
        _logger.d(remark)
        _logger.d(options)
        answer_list = self._course.find_detail_by_assist_word(assist_word)
        _logger.d(answer_list)
        if len(answer_list) == 0:
            raise AnswerNotFoundException(13)
        for answer in answer_list:
            for content in answer["content"]:
                if adapter.is_remark_or_sentence_in_example(content["example"], remark, sentence):
                    #   创建一个临时列表，方便下一步判断答案
                    tem_list = []
                    for key in content["example"]:
                        if key != remark:   # 本题是根据题目例句选择与例句同列的例句，故需排除题目例句本身
                            tem_list.append(content["example"][key])
                    for sentence in options:
                        if sentence["content"] in tem_list:
                            _logger.d(sentence["content"])
                            return str(sentence["answer_tag"])
                    for sentence in options:
                        if Tool.is_str_in_list_by_some_difference(sentence["content"], tem_list):
                            _logger.d(sentence["content"])
                            return str(sentence["answer_tag"])
        raise AnswerNotFoundException(13)

    # 16、21、22与其处理方式一致
    # word 单词原型，精确匹配，效率极高
    # options 题目选项
    def find_answer_by_15(self, word: str, options: list) -> str:
        _logger.d("\nfind_answer_by_15")
        _logger.d(word)
        _logger.d(options)
        answer = self._course.find_detail_by_word(word)
        _logger.d(answer)
        if answer is None:
            raise AnswerNotFoundException(15)
        #   创建一个临时列表
        tem_list = []
        for content in answer["content"]:
            tem_list.extend(adapter.process_word_mean(content["mean"]))
        tem_set = set(tem_list)
        for mean in options:
            if len(tem_set & set(adapter.process_option_mean(mean["content"]))) != 0:
                return str(mean["answer_tag"])
        vague_answer = adapter.answer_15_1(tem_list, options)
        if vague_answer:
            return vague_answer
        raise AnswerNotFoundException(15)

    # 18与其处理方式一致
    # content 单词词义
    # options 题目选项
    def find_answer_by_17(self, content: str, options: list) -> str:
        _logger.d("\nfind_answer_by_17")
        _logger.d(content)
        content = re.sub(r'\s\s', ' ', content)
        _logger.d(content)
        _logger.d(options)
        content_list = adapter.process_option_mean(content)
        # 21.3.17修复由群友转交给115***706提交的BUG，我们仍未知道那天是哪位群友的贡献
        if content.find("（") != -1:
            content_list.extend(adapter.process_option_mean(re.sub(r"（.+）", "", content)))
        # 感谢群友104***629提供的错误日志让我意识到了使用了错误的适配函数
        content_set = set(content_list)
        for word in options:
            answer = self._course.find_detail_by_word(word["content"])
            _logger.d(answer)
            if answer is None:  # 选项中可能存在不在课程中的单词，故查询结果可能为空
                continue
            # 创建一个临时列表
            tem_list = []
            for mean in answer["content"]:
                tem_list.extend(adapter.process_word_mean(mean["mean"]))
            if len(set(tem_list) & content_set) != 0:
                return str(word["answer_tag"])
        # 模糊匹配
        answer_dict = {}
        for word in options:
            answer = self._course.find_detail_by_word(word["content"])
            _logger.d(answer)
            if answer:  # 选项中可能存在不在课程中的单词，故查询结果可能为空
                answer_dict[word["content"]] = answer
        vague_answer = adapter.answer_17_1(content_list, options, answer_dict)
        if vague_answer:
            return vague_answer
        raise AnswerNotFoundException(17)

    # 无需兼容，本身即可得出答案，最让人安心的一个
    @staticmethod
    def find_answer_by_31(remark: list, options: list) -> list:
        _logger.d("\find_answer_by_31")
        _logger.d(options)
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
    def find_answer_by_32(self, remark: str, options: list, blank_count: int, skip_times: int) -> str:
        _logger.d("\nfind_answer_by_32")
        _logger.d(remark)
        _logger.d(options)
        _logger.d(f"{blank_count:d}")
        # 选项预处理
        option_list = []  # 存放选项中的短语，短语由规定顺序的单词数组构成
        for usage in options:
            content, _ = adapter.process_content_and_remark(usage["content"], None)
            _logger.d(content, is_show=False)
            option_list.extend(re.split(r"\s+", adapter.process_option_usage(content)))
        _logger.d(option_list, is_show=False)
        option_set = Set(option_list)
        wrong_set = set()

        for key, value in self._course.data.items():
            for content in value["content"]:
                usage_list = content["usage"].get(remark) or adapter.usage_get_remark(content["usage"], remark)
                if usage_list is not None:
                    _logger.d(usage_list, is_show=False)
                    for usage in usage_list:
                        if len(option_set & Set(usage)) == len(usage):
                            if skip_times != 0 or adapter.answer_32_2(options, usage) in wrong_set:
                                skip_times -= 1
                                wrong_set.add(adapter.answer_32_2(options, usage))
                                continue
                            if len(usage) == blank_count:
                                # 因原选项中可能会出现多出空格问题
                                return adapter.answer_32_2(options, usage)
                            # 修复题库中同时存在
                            # "迫切需要": ["an", "urgent", "need"]
                            # "迫切需要": ["urgent", "need"]
                            # 导致的答案匹配出错，该BUG由群友183***092提供，156行为其贡献
                            if len(usage) > blank_count:
                                # 下列情况为一个选项中存在多个单词（说好的一个单词一个选项呢？？？）
                                result = adapter.answer_32_1(options, usage)
                                if result:
                                    return result
        raise AnswerNotFoundException(32)

    # 42与其处理方式一致
    # content 英语例句
    # remark 例句的翻译
    # options 题目选项
    def find_answer_by_41(self, content: str, remark: str, options: list) -> str:
        _logger.d("\nfind_answer_by_41")
        _logger.d(content)
        content = adapter.process_option_sentence(content)  # 合着您传输多个空格就为了增加网页端单词间距显示？？？
        _logger.d(content)
        _logger.d(options)
        for word in options:
            answer_list = self._course.find_detail_by_assist_word(word["content"])
            if len(answer_list) == 0:
                continue
            for answer in answer_list:
                _logger.d(answer)
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
        _logger.d("\nfind_answer_by_43")
        _logger.d(content)
        content = adapter.process_option_sentence(content)  # 合着您传输多个空格就为了增加网页端单词间距显示？？？
        _logger.d(content)
        _logger.d(options)
        for option in options:
            answer = self._course.find_detail_by_word(option["content"])
            if answer is None:
                continue
            _logger.d(answer)
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
    # skip_times 跳过成功匹配答案的次数
    def find_answer_by_51(self, content: str, remark: str, skip_times: int) -> str:
        _logger.d("\nfind_answer_by_51")
        _logger.d(content)
        _logger.d(remark)
        content, remark = adapter.process_content_and_remark(content, remark)
        usage_list = adapter.process_option_usage(content).split(" ")
        usage_list_set = Set(usage_list)
        _logger.d(usage_list)
        remark_set = set(adapter.process_option_mean(remark))
        for key, value in self._course.data.items():
            if len(usage_list) == 1:
                for i in value["content"]:
                    if len(remark_set & set(adapter.process_word_mean(i["mean"]))) != 0:
                        if skip_times != 0:
                            skip_times -= 1
                            continue
                        return key
            else:
                for content_list in value["content"]:
                    usages = content_list["usage"].get(remark)\
                             or adapter.usage_get_remark(content_list["usage"], remark)
                    if usages is not None:
                        _logger.d(usages)
                        for usage in usages:
                            # 修复长度判断，该bug由群友169***762提供
                            if len(usage_list) - 1 != len(usage_list_set & Set(usage))\
                                    or len(usage_list) != len(usage):
                                continue
                            for index, word in enumerate(usage):
                                if word != usage_list[index]:
                                    if skip_times != 0:
                                        skip_times -= 1
                                        continue
                                    # 原本只需返回usage[index]即可
                                    # 但因兼容CET4_3的at one's {}'s end(智穷力竭)特殊案例，不得不复杂化
                                    return adapter.answer_51(usage_list[index], usage[index])
        vague_answer = adapter.answer_51_1(self._course.data, remark, skip_times, usage_list, usage_list_set)
        if vague_answer:
            return vague_answer
        raise AnswerNotFoundException(51)

    # 54与其处理方式一致
    # content 英语例句
    # remark 例句翻译
    def find_answer_by_53(self, content: str, remark: str) -> str:
        _logger.d("\nfind_answer_by_53")
        _logger.d(content)
        _logger.d(remark)
        content = adapter.process_option_sentence(content)
        _logger.d(content)
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
