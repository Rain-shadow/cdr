#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-19, 0019 21:18
# @Author: 佚名
# @File  : course.py
import asyncio
import json
import re
import os
from asyncio.exceptions import CancelledError

from cdr.aio import aiorequset as requests
from cdr.exception import NoPermission, NoSupportVersionException
from cdr.utils import Set
from .setting import _settings
from .log import Log
from .tool import Tool
from cdr.config import CDR_VERSION, DATA_DIR_PATH

_settings = _settings
_logger = Log.get_logger()
debug_word = None


class Course:
    DATA_VERSION = 14

    __PATTERN = re.compile(r"([0-9A-Za-z.\s(){}'/&‘’,（）…-]*)?\s(.*)")
    #  适配课程[QXB_3]中指定章节[QXB_3_3_A]单词[insecure]中某个短语引起的短语翻译匹配错误问题
    #  {insecure} factors 不稳定因素 不稳定因素
    #  该BUG由群友604***887提供的日志
    __USAGE_REPEAT_MEAN_PATTERN = re.compile(r"((?:(?!\s).)*)(?:\s?\1)?")
    __IS_MORE = re.compile(r"(.*…)\s(…[^a-zA-Z]*)")

    def __init__(self, course_id: str):
        self.id = course_id
        self.data = {}
        self._headers = {
            "Host": "gateway.vocabgo.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Requested-With": "XMLHttpRequest",
            "UserToken": _settings.user_token,
            "User-Agent": _settings.user_agent,
            "Origin": "https://app.vocabgo.com",
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=utf-8",
            "Referer": "https://app.vocabgo.com/overall/",
            "TE": "Trailers"
        }
        self.is_success = True
        self._fail_list = {}

    async def load_word(self):
        is_show = not _settings.is_multiple_chapter
        if self._load_local_answer():
            return
        _logger.i("从网络装载题库中......(10s-30s)", is_show=is_show)
        #   获取课程所有列表
        data = {
            "course_id": self.id,
            "timestamp": Tool.time(),
            "versions": CDR_VERSION
        }
        res = await requests.get("https://gateway.vocabgo.com/Teacher/Course/UnitList",
                                 params=data, headers=self._headers, timeout=_settings.timeout)
        json_data = (await res.json())["data"]["course_list_info_list"]
        res.close()
        chapter_words = {}
        task_list = []
        for m_list in json_data:
            #   根据课程id及列表id获取所有单词
            task_list.append(self._get_course_chapter_word_list(m_list["list_id"]))
        # noinspection PyTypeChecker
        results: list = await asyncio.gather(*task_list)
        for list_id, words in results:
            chapter_words[list_id] = words
        task_list.clear()
        for list_id, words in chapter_words.items():
            for word in words:
                task_list.append(self._get_word_info_and_dispose(list_id, word))
        try:
            await asyncio.gather(*task_list)
        except CancelledError as e:
            pass
        if self._fail_list:
            self.is_success = True
            for list_id, words in results:
                chapter_words[list_id] = words
            task_list.clear()
            for list_id, words in chapter_words.items():
                for word in words:
                    task_list.append(self._get_word_info_and_dispose(list_id, word))
            await asyncio.gather(*task_list)
        if self.is_success:
            with open(DATA_DIR_PATH + self.id, mode='w', encoding='utf-8') as answer:
                tem = {
                    "courseId": self.id,
                    "data": self.data,
                    "version": Course.DATA_VERSION
                }
                answer.write(json.dumps(tem))
                answer.close()
            _logger.i("本次题库已成功保存", is_show=is_show)
        else:
            _logger.i("有单词未能成功加载，这会导致答案匹配率下降且本次不会保存题库", is_show=is_show)
            _logger.i("你可以等待网络通畅后继续答题", is_show=is_show)

    def _load_local_answer(self) -> bool:
        if not os.path.exists(DATA_DIR_PATH + self.id):
            return False
        with open(DATA_DIR_PATH + self.id, mode='r', encoding='utf-8') as answer:
            data = json.loads(answer.read())
            answer.close()
            if data["version"] < Course.DATA_VERSION:
                _logger.i("本地题库版本低于软件指定词库版本，稍后将重新从网络加载题库")
                return False
            _logger.i("复用上次本地缓存题库")
            self.data = data["data"]
            return True

    async def _get_course_chapter_word_list(self, list_id: str):
        course_id = self.id
        timeout = _settings.timeout
        data = {
            "config_id": -1,
            "course_id": course_id,
            "list_id": list_id,
            "timestamp": Tool.time(),
            "versions": CDR_VERSION
        }
        res = await requests.get("https://gateway.vocabgo.com/Teacher/Course/UnitWordList",
                                 headers=self._headers, params=data, timeout=timeout)
        word_list = (await res.json())["data"]["word_list"]
        res.close()
        return list_id, word_list

    async def _get_word_info_and_dispose(self, list_id: str, word: str, is_second: bool = False):
        asyncio.current_task().set_name(f"{list_id}_{word}")
        try:
            answer = await self.get_detail_by_word(self.id, list_id, word)
        except NoPermission:
            _logger.i(f"[{self.id}/{list_id}]疑似vip课程章节，无权访问，跳过该章节答案加载，本次不会缓存本地词库")
            self.is_success = False
            for task in asyncio.all_tasks():
                name = task.get_name()
                if name.find(list_id) != -1:
                    task.cancel()
            return
        except NoSupportVersionException as e:
            _logger.e(e)
            _logger.e(f"[{self.id}]答案加载出错，本次不会缓存本地词库")
            self.is_success = False
            for task in asyncio.all_tasks():
                task.cancel()
            return
        except CancelledError as e:
            return
        except Exception as e:
            print(e)
            _logger.e(e.__traceback__.tb_frame.f_globals["__file__"], is_show=False)
            _logger.e(e.__traceback__.tb_lineno, is_show=False)
            if not is_second:
                _logger.w(f"警告！单词：{word}({self.id}/{list_id})加载失败，稍后软件将会尝试二次加载")
            else:
                _logger.w(f"警告！单词：{word}({self.id}/{list_id})二次加载失败，本次不会缓存本地词库")
            self.is_success = False
            if self._fail_list.get(list_id) is None:
                self._fail_list[list_id] = [word]
            else:
                self._fail_list[list_id].append(word)
            return
        else:
            if is_second:
                _logger.d(f"单词：{word}二次加载成功！")
        if self.data.get(word) is None:
            self.data[word] = answer
        else:
            # 废弃代码self.data[word]["content"].extend(answer["content"])
            # 存在单词翻译相同情况，该BUG由群友104***748提供，若不处理，会让题型32的特殊情况出现问题
            tem_map = {}
            for index, item in enumerate(self.data[word]["content"]):
                tem_map[item["mean"]] = index
            for item in answer["content"]:
                mean = tem_map.get(item["mean"])
                if mean is None:
                    self.data[word]["content"].append(item)
                else:
                    tem_data = self.data[word]["content"][mean]
                    for key in item["usage"]:
                        if tem_data["usage"].get(key) is None:
                            tem_data["usage"][key] = item["usage"][key]
                        else:
                            tem_list = []
                            for item_usage in item["usage"][key]:
                                has_repetition = False
                                item_usage_set = Set(item_usage)
                                for usage in tem_data["usage"][key]:
                                    if len(Set(usage) & item_usage_set) == len(usage):
                                        has_repetition = True
                                        break
                                if not has_repetition:
                                    tem_list.append(item_usage)
                            tem_data["usage"][key].extend(tem_list)
                    for key in item["example"]:
                        if tem_data["example"].get(key) is None:
                            tem_data["example"][key] = item["example"][key]
            del tem_map
            self.data[word]["assist"].extend(answer["assist"])
        self.data[word]["assist"] = list(set(self.data[word]["assist"]))

    def find_detail_by_word(self, word):
        return self.data.get(word) or self.data.get(word.lower())

    def find_detail_by_assist_word(self, word):
        tem_list = []
        for key in self.data:
            if word in self.data[key]["assist"] or word.lower() in self.data[key]["assist"]:
                tem_list.append(self.data[key])
        return tem_list

    @staticmethod
    def get_more_usage(usage: list, aim_word: str):
        compatible_word = [
            ["sth", "something"],
            ["sb", "somebody"],
        ]
        # 该转换为单向转换，由value[0] -> value[1]转换
        compatible_word_map = {
            # 什么？你说这两个毫无关联，我为什么要添加这两个？
            # 哦宝贝，你为什么不去看看 【CET6 List 01】的单词【allure】其短语【失去魅力】是什么呢，它出的对应的题又是什么呢
            "allure": ["lose", "loose"],
            "immigrant": ["illegal", "illigal"],    # 由群友839***272提交的错误日志得到
        }
        tem_list = [usage]
        tem_str = "#".join(usage)
        flag = False
        for cw in compatible_word:
            word_list = list(set(cw) & set(usage))
            if len(word_list) != 0:
                aim = cw[0] if cw.index(word_list[0]) == 1 else cw[1]
                tem_str = tem_str.replace(word_list[0], aim)
                flag = True
        if flag:
            tem_list.append(tem_str.split("#"))
        for key, value in compatible_word_map.items():
            if key == aim_word and value[0] in usage:
                tem_list.append("#".join(usage).replace(value[0], value[1]).split("#"))
        return tem_list

    @staticmethod
    def remove_word_in_usage(usage: list, aim_word: str, remark: str):
        compatible_word = [
            ["legitimate", "合法政府", ["a"]],
        ]
        tem_list = []
        for value in compatible_word:
            if value[0] == aim_word and value[1] == remark:
                tem_list.append(list(set(usage) - set(value[2])))
        return tem_list

    # 强行适配CET6_hx_12中单词reconcile题型32
    @staticmethod
    def force_add_usage(aim_word: str, remark: str):
        compatible_word = [
            ["reconcile", "使A与B和好", [
                ['reconcile', 'with', 'somebody/', 'reconcile', 'A', 'with', 'B']
            ]],
        ]
        tem_list = []
        for value in compatible_word:
            if value[0] == aim_word and value[1] == remark:
                tem_list.extend(value[2])
        return tem_list

    @staticmethod
    def process_data(data: dict, version: int) -> list:
        if version == 1:
            result = []
            for v in data["options"]:
                result.append(v["content"])
            return result
        elif version == 2:
            return data["means"]
        raise NoSupportVersionException("答案解析", version)

    @staticmethod
    def process_mean(content_data, version: int) -> str:
        if version == 1:
            return content_data["mean"]
        elif version == 2:
            #   版本2当中将词性与翻译分割成了数组
            return ' '.join(content_data["mean"])
        raise NoSupportVersionException("答案解析", version)

    @staticmethod
    def process_usage(content_data: dict, version: int) -> list:
        result = []
        if version == 1:
            phrases = content_data["usage"]
        elif version == 2:
            phrases = []
            for mix in content_data["usages"]:
                phrases.extend(mix["phrases"])
                phrase = mix["usage"]
                if phrase is None or len(phrase["eg"]) == 0:
                    continue
                result.append({
                    "key": phrase["cn"],
                    "value": re.sub(r"</?.*?>|[{}()]", "", phrase["eg"]).split(" ")
                })
        else:
            raise NoSupportVersionException("答案解析", version)
        for phrase in phrases:
            phrase = re.sub(r"[\ue000-\uefff]", "", phrase)
            if Course.__IS_MORE.match(phrase) is None:
                matcher = Course.__PATTERN.match(phrase)
            else:
                matcher = re.match(r"([0-9A-Za-z.\s(){}'/&‘’,（）…-]*)?\s(….*)", phrase)
            if matcher is None:
                print(phrase)

            usage_value = re.sub(r"[{}()]", "", matcher.group(1))
            usage_value = re.sub(r"[.…,-]", " ", usage_value)
            #   处理因清理"..."而造成的多余空格
            usage_value = " ".join(usage_value.split()).split(" ")
            usage_key = matcher.group(2).strip()
            if Course.__USAGE_REPEAT_MEAN_PATTERN.fullmatch(usage_key) is not None:
                usage_key = Course.__USAGE_REPEAT_MEAN_PATTERN.match(usage_key).group(1)
            result.append({
                "key": usage_key,
                "value": usage_value
            })
        return result

    @staticmethod
    def process_example(content_data: dict, version: int) -> list:
        result = []
        if version == 1:
            for example in content_data["example"]:
                result.append({
                    "key": example["sen_mean_cn"],
                    "value": example["sen_content"]
                })
        elif version == 2:
            for mix in content_data["usages"]:
                if mix["examples"] is None:
                    continue
                for example in mix["examples"]:
                    result.append({
                        "key": example["sen_mean_cn"],
                        "value": example["sen_content"]
                    })
        else:
            raise NoSupportVersionException("答案解析", version)
        return result

    @staticmethod
    async def get_detail_by_word(course_id, list_id, word):
        timeout = _settings.timeout
        data = {
            "course_id": course_id,
            "list_id": list_id,
            "word": word,
            "timestamp": Tool.time(),
            "versions": CDR_VERSION
        }
        (await requests.options(
            url='https://gateway.vocabgo.com/Student/Course/StudyWordInfo',
            params=data,
            headers=_settings.header,
            timeout=timeout)).close()
        res = await requests.get(
            url='https://gateway.vocabgo.com/Student/Course/StudyWordInfo',
            params=data,
            headers=_settings.header,
            timeout=timeout)

        data = await res.json()
        if word == debug_word:
            print(data)
        if data["code"] == 0 and data["msg"] == "没有权限":
            raise NoPermission(data["msg"])
        data = data["data"]
        res.close()
        answer = {
            "content": [],
            "assist": []
        }
        data_version = int(data["version"])
        for content in Course.process_data(data, data_version):
            tem_dict = {}
            #   统一词义格式：1.多空格去除为1空格 2.删除中文括号中的附加内容
            c_str = ' '.join(Course.process_mean(content, data_version).split())
            while c_str.find("（") != -1:
                c_str = c_str[:c_str.find("（")] + c_str[c_str.find("）") + 1:]
            tem_dict["mean"] = ' '.join(c_str.split())
            del c_str
            tem_dict["usage"] = {}
            tem_dict["example"] = {}
            #   辅助单词列表，存放当前单词例句中的不同时态
            #   处理答案
            for usage in Course.process_usage(content, data_version):
                #   因不同短语可能具有相同的翻译，需做额外处理
                if tem_dict["usage"].get(usage["key"]) is None:
                    tem_dict["usage"][usage["key"]] = []
                tem_dict["usage"][usage["key"]].extend(Course.get_more_usage(usage["value"], word))
                tem_dict["usage"][usage["key"]].extend(
                    Course.remove_word_in_usage(usage["value"], word, usage["key"])
                )
                tem_dict["usage"][usage["key"]].extend(Course.force_add_usage(word, usage["key"]))
            for example in Course.process_example(content, data_version):
                value = example["value"]
                tem_dict["example"][example["key"]] = value
                assist_word = value[value.find("{") + 1: value.find("}")]
                if assist_word not in answer["assist"]:
                    answer["assist"].append(assist_word)
            answer["content"].append(tem_dict)
        return answer
