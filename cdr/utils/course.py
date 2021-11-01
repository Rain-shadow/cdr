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
from cdr.request.network_error import NetworkError

_settings = _settings
_logger = Log.get_logger()
_lock = asyncio.locks.Lock()
debug_word = None


class Course:
    DATA_VERSION = 15

    __PATTERN = re.compile(r"([0-9A-Za-z.\s(){}'/&‘’,（）…-]*)?\s(.*)")
    #  适配课程[QXB_3]中指定章节[QXB_3_3_A]单词[insecure]中某个短语引起的短语翻译匹配错误问题
    #  {insecure} factors 不稳定因素 不稳定因素
    #  该BUG由群友604***887提供的日志
    __USAGE_REPEAT_MEAN_PATTERN = re.compile(r"((?:(?!\s).)*)(?:\s?\1)?")
    __IS_MORE = re.compile(r"(.*…)\s(…[^a-zA-Z]*)")
    __HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=utf-8",
        "UserToken": _settings.user_token,
        "User-Agent": _settings.user_agent,
    }

    __CREATE_KEY = object()

    def __init__(self, create_key):
        assert create_key == Course.__CREATE_KEY, "Course objects must be created using Course.load_course"
        self.data = {}

    def find_detail_by_word(self, word):
        return self.data.get(word) or self.data.get(word.lower())

    def find_detail_by_assist_word(self, word):
        tem_list = []
        for key in self.data:
            if word in self.data[key]["assist"] or word.lower() in self.data[key]["assist"]:
                tem_list.append(self.data[key])
        return tem_list

    @classmethod
    async def load_course(cls, *, course_id: str = None, words: list[tuple[str, str, str]] = None):
        """
        参数二选一，通过指定的参数返回一个Course对象
        :param course_id: 设置该参数将加载该课程下的所有单词
        :param words: 设置该参数将仅加载指定的单词作为题库查询依据
        :return:
        """
        # 不加这行会导致某些情况下身份授权出现问题
        cls.__HEADERS["UserToken"] = _settings.user_token
        result = Course(cls.__CREATE_KEY)
        await result._load_answer(course_id, words)
        return result

    async def _load_answer(self, course_id: str, words: list[tuple[str, str, str]]):
        is_show = not _settings.is_multiple_chapter
        need_load = set()
        if course_id is not None:
            result = Course._get_local_answer(course_id)
            if result is not None:
                _logger.i(f"复用上次本地缓存题库，题库id：{course_id}", is_show=is_show)
                self.data = result
                return
            need_load.add(course_id)
            words = await Course._get_words_by_course_id(course_id)

        from itertools import groupby
        group_word = {}
        # 先排序，再分组。groupby函数才能正常起到分组作用
        for key, group in groupby(sorted(words, key=lambda o: o[0]), key=lambda o: o[0]):
            group_word[key] = list(group)
            result = Course._get_local_answer(key)
            if result is None:
                need_load.add(key)
                continue
            _logger.i(f"复用上次本地缓存题库(题库id：{key})", is_show=is_show)
            for _, _, word in group_word[key]:
                await Course._merger_answer(self.data, word, result[word])
        # 不要奇怪一个任务会出现多个课程的情况，《自建词表》它就这尿性
        # task_list = []
        # for course_id in need_load:
        #     task_list.append(self._load_from_network(course_id, group_word))
        # await asyncio.gather(*task_list)

        for course_id in need_load:
            await self._load_from_network(course_id, group_word)

    async def _load_from_network(self, course_id: str, group_word: dict):
        is_show = not _settings.is_multiple_chapter
        _logger.i(f"从网络装载题库中(题库id：{course_id})......(10s-30s)", is_show=is_show)
        answer = {}
        task_list = []
        for course_id, list_id, word in (await Course._get_words_by_course_id(course_id)):
            task_list.append(Course._get_word_info_and_dispose(course_id, list_id, word))
        # noinspection PyTypeChecker
        results: list = await asyncio.gather(*task_list)
        # 题库合并
        flag = True
        for word, result, is_success in results:
            if not is_success:
                flag = False
                continue
            await Course._merger_answer(answer, word, result)
        # 从题库中获取所需单词
        for _, list_id, word in group_word[course_id]:
            # flag为False时，所需目标单词可能未能成功加载
            if answer.get(word):
                await Course._merger_answer(self.data, word, answer[word])
            else:
                _logger.w(f"警告！单词：{word}({course_id}/{list_id})加载失败，这会导致答案匹配率下降")
        if flag:
            # 题库保存至本地
            with open(DATA_DIR_PATH + course_id, mode='w', encoding='utf-8') as answer_file:
                tem = {
                    "courseId": course_id,
                    "data": answer,
                    "version": Course.DATA_VERSION
                }
                answer_file.write(json.dumps(tem))
                answer_file.close()
            _logger.i(f"本次题库已成功保存(题库id：{course_id})", is_show=is_show)
        else:
            _logger.i(f"有单词未能成功加载，本次不会保存题库(题库id：{course_id})", is_show=is_show)

    @staticmethod
    async def _merger_answer(answer_data: dict, word: str, new_answer: dict):
        """合并题库"""
        await _lock.acquire()
        if answer_data.get(word) is None:
            answer_data[word] = new_answer
            _lock.release()
            return
        # 废弃代码self.data[word]["content"].extend(answer["content"])
        # 存在单词翻译相同情况，该BUG由群友104***748提供，若不处理，会让题型32的特殊情况出现问题
        mean_map: dict[str: int] = {}
        for index, content in enumerate(answer_data[word]["content"]):
            mean_map[content["mean"]] = index
        for content in new_answer["content"]:
            # 判断是否存在相同翻译
            if content["mean"] not in mean_map.keys():
                answer_data[word]["content"].append(content)
                continue
            # 相同翻译存在，获取源数据
            index = mean_map[content["mean"]]
            tem_data = answer_data[word]["content"][index]
            # 相同短语翻译处理
            for key in content["phrase"]:
                if tem_data["phrase"].get(key) is None:
                    tem_data["phrase"][key] = content["phrase"][key]
                    continue
                phrase_list = []
                for item_usage in content["phrase"][key]:
                    has_repetition = False
                    item_usage_set = Set(item_usage)
                    for usage in tem_data["phrase"][key]:
                        if len(Set(usage) & item_usage_set) == len(usage):
                            has_repetition = True
                            break
                    if not has_repetition:
                        phrase_list.append(item_usage)
                tem_data["phrase"][key].extend(phrase_list)
            # 仅添加例句翻译不同的题库
            for key in content["example"]:
                if tem_data["example"].get(key) is None:
                    tem_data["example"][key] = content["example"][key]
        answer_data[word]["assist"].extend(new_answer["assist"])
        # 辅助词去重
        answer_data[word]["assist"] = list(set(answer_data[word]["assist"]))
        _lock.release()

    @classmethod
    def _get_local_answer(cls, course_id: str):
        if not os.path.exists(DATA_DIR_PATH + course_id):
            return None
        with open(DATA_DIR_PATH + course_id, mode='r', encoding='utf-8') as answer_file:
            data = json.loads(answer_file.read())
            answer_file.close()
            if data["version"] != cls.DATA_VERSION:
                _logger.i(f"本地题库版本与软件指定词库版本不匹配(题库id：{course_id})，稍后将重新从网络加载题库")
                return None
            return data["data"]

    @classmethod
    async def _get_words_by_course_id(cls, course_id: str) -> list[tuple[str, str, str]]:
        """
        根据课程id获取对应的单词列表
        :param course_id:
        :return:
        """
        result = []
        try:
            # 一次性获取对应课程下的所有单词
            res = await requests.get(f"https://resource.vocabgo.com/Resource/CoursePage/{course_id}.json",
                                     timeout=_settings.timeout)
            json_data = await res.json()
            res.close()
            for word_info in json_data:
                result.append((word_info["course_id"], word_info["list_id"], word_info["word"]))
            return result
        except NetworkError:
            # 多次网络请求（先获取对应课程的列表，再获取列表下的单词）
            # 获取课程所有列表
            data = {
                "course_id": course_id,
                "timestamp": Tool.time(),
                "versions": CDR_VERSION
            }
            res = await requests.get("https://gateway.vocabgo.com/Teacher/Course/UnitList",
                                     params=data, headers=cls.__HEADERS, timeout=_settings.timeout)
            json_data = await res.json()
            json_data = json_data["data"]["course_list_info_list"]
            res.close()
            task_list = []
            for m_list in json_data:
                task_list.append(cls._get_words_by_course_chapter(course_id, m_list["list_id"]))
            # noinspection PyTypeChecker
            results: list = await asyncio.gather(*task_list)
            for item in results:
                result.extend(item)
            return result

    @classmethod
    async def _get_words_by_course_chapter(cls, course_id: str, list_id: str) -> list[tuple[str, str, str]]:
        """
        根据课程id和章节id获取对应的单词列表
        :param course_id:
        :param list_id:
        :return:
        """
        data = {
            "course_id": course_id,
            "list_id": list_id,
            "timestamp": Tool.time(),
            "versions": CDR_VERSION
        }
        res = await requests.get("https://gateway.vocabgo.com/Teacher/Course/UnitWordList",
                                 headers=cls.__HEADERS, params=data, timeout=_settings.timeout)
        word_list = (await res.json())["data"]["word_list"]
        res.close()

        result = []
        for word in word_list:
            result.append((course_id, list_id, word))
        return result

    @classmethod
    async def _get_word_info_and_dispose(cls, course_id: str, list_id: str, word: str, is_second: bool = False) \
            -> tuple[str, dict, bool]:
        """获取对应单词的信息并处理成软件所需的标准格式"""
        asyncio.current_task().set_name(f"{list_id}_{word}")
        try:
            answer = await cls._get_detail_by_word(course_id, list_id, word)
        except NoPermission:
            _logger.i(f"[{course_id}/{list_id}]疑似vip课程章节，无权访问，跳过该章节答案加载，本次不会缓存本地词库")
            for task in asyncio.all_tasks():
                name = task.get_name()
                if name.find(list_id) != -1:
                    task.cancel()
            return word, None, False
        except NoSupportVersionException as e:
            _logger.e(e)
            _logger.e(f"[{course_id}]答案加载出错，本次不会缓存本地词库")
            for task in asyncio.all_tasks():
                task.cancel()
            return word, None, False
        except CancelledError as e:
            return word, None, False
        except Exception as e:
            _logger.e(f"File \"{e.__traceback__.tb_frame.f_globals['__file__']}\", line {e.__traceback__.tb_lineno}",
                      is_show=False)
            _logger.w(f"警告！单词：{word}({course_id}/{list_id})加载失败", is_show=False)
            # if not is_second:
            #     _logger.w(f"警告！单词：{word}({course_id}/{list_id})加载失败，稍后软件将会尝试二次加载")
            # else:
            #     _logger.w(f"警告！单词：{word}({course_id}/{list_id})二次加载失败，本次不会缓存本地词库")
            return word, None, False
        else:
            if is_second:
                _logger.d(f"单词：{word}二次加载成功！")
            return word, answer, True

    @staticmethod
    def _get_more_phrase(phrase: list, aim_word: str) -> list[list[str]]:
        compatible_word = [
            ["sth", "something"],
            ["sb", "somebody"],
        ]
        # 该转换为单向转换，由value[0] -> value[1]转换
        compatible_word_map = {
            # 什么？你说这两个毫无关联，我为什么要添加这两个？
            # 哦宝贝，你为什么不去看看 【CET6 List 01】的单词【allure】其短语【失去魅力】是什么呢，它出的对应的题又是什么呢
            "allure": ["lose", "loose"],
            "immigrant": ["illegal", "illigal"],  # 由群友839***272提交的错误日志得到
        }
        tem_list = [phrase]
        tem_str = "#".join(phrase)
        flag = False
        for cw in compatible_word:
            word_list = list(set(cw) & set(phrase))
            if len(word_list) != 0:
                aim = cw[0] if cw.index(word_list[0]) == 1 else cw[1]
                tem_str = tem_str.replace(word_list[0], aim)
                flag = True
        if flag:
            tem_list.append(tem_str.split("#"))
        for key, value in compatible_word_map.items():
            if key == aim_word and value[0] in phrase:
                tem_list.append("#".join(phrase).replace(value[0], value[1]).split("#"))
        return tem_list

    @staticmethod
    def _remove_word_in_phrase(phrase: list, aim_word: str, remark: str):
        compatible_word = [
            ["legitimate", "合法政府", ["a"]],
        ]
        tem_list = []
        for value in compatible_word:
            if value[0] == aim_word and value[1] == remark:
                tem_list.append(list(set(phrase) - set(value[2])))
        return tem_list

    # 强行适配CET6_hx_12中单词reconcile题型32
    @staticmethod
    def _force_add_phrase(aim_word: str, remark: str):
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
    def _process_data(data: dict, version: int) -> list:
        if version == 1:
            result = []
            for v in data["options"]:
                result.append(v["content"])
            return result
        elif version == 2:
            return data["means"]
        raise NoSupportVersionException("答案解析", version)

    @staticmethod
    def _process_mean(content_data, version: int) -> str:
        if version == 1:
            return content_data["mean"]
        elif version == 2:
            #   版本2当中将词性与翻译分割成了数组
            return ' '.join(content_data["mean"])
        raise NoSupportVersionException("答案解析", version)

    @classmethod
    def _process_phrase(cls, content_data: dict, version: int) -> list:
        result = []
        if version == 1:
            phrases = content_data["usage"]
        elif version == 2:
            phrases = []
            for mix in content_data["usages"]:
                phrases.extend(mix["phrases"])
                phrase = mix["usage"]
                if phrase is None:
                    continue
                if len(phrase["eg"]) != 0:
                    result.append({
                        "key": phrase["cn"],
                        "value": re.sub(r"</?.*?>|[{}()]", "", phrase["eg"]).split(" ")
                    })
                if len(phrase["text"]) != 0:
                    phrase_value = re.sub(r"[{}()]|noun|prep|pron|verb|conj|ad[jv]?", "", phrase["text"])
                    phrase_value = re.sub(r"[.…,-]", " ", phrase_value)
                    #   处理因清理"..."而造成的多余空格
                    phrase_value = " ".join(phrase_value.split())
                    if len(phrase_value.split(" ")) <= 1:
                        continue
                    result.append({
                        "key": phrase["cn"],
                        "value": phrase_value.split(" ")
                    })
        else:
            raise NoSupportVersionException("答案解析", version)
        for phrase in phrases:
            phrase = re.sub(r"[\ue000-\uefff]", "", phrase)
            if cls.__IS_MORE.match(phrase) is None:
                matcher = cls.__PATTERN.match(phrase)
            else:
                matcher = re.match(r"([0-9A-Za-z.\s(){}'/&‘’,（）…-]*)?\s(….*)", phrase)
            if matcher is None:
                print(phrase)

            phrase_value = re.sub(r"[{}()]", "", matcher.group(1))
            phrase_value = re.sub(r"[.…,-]", " ", phrase_value)
            #   处理因清理"..."而造成的多余空格
            phrase_value = " ".join(phrase_value.split())
            phrase_key = matcher.group(2).strip()
            if cls.__USAGE_REPEAT_MEAN_PATTERN.fullmatch(phrase_key) is not None:
                phrase_key = cls.__USAGE_REPEAT_MEAN_PATTERN.match(phrase_key).group(1)
            result.append({
                "key": phrase_key,
                "value": phrase_value.split(" ")
            })
        return result

    @staticmethod
    def _process_example(content_data: dict, version: int) -> list:
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

    @classmethod
    async def _get_detail_by_word(cls, course_id, list_id, word):
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
            "assist": [],
        }
        data_version = int(data["version"])
        for content in cls._process_data(data, data_version):
            tem_dict = {}
            #   统一词义格式：1.多空格去除为1空格 2.删除中文括号中的附加内容
            c_str = ' '.join(cls._process_mean(content, data_version).split())
            while c_str.find("（") != -1:
                c_str = c_str[:c_str.find("（")] + c_str[c_str.find("）") + 1:]
            tem_dict["mean"] = ' '.join(c_str.split())
            del c_str
            tem_dict["phrase"] = {}
            tem_dict["example"] = {}
            #   辅助单词列表，存放当前单词例句中的不同时态
            #   处理答案
            for phrase in cls._process_phrase(content, data_version):
                #   因不同短语可能具有相同的翻译，需做额外处理
                if tem_dict["phrase"].get(phrase["key"]) is None:
                    tem_dict["phrase"][phrase["key"]] = []
                tem_dict["phrase"][phrase["key"]].extend(cls._get_more_phrase(phrase["value"], word))
                tem_dict["phrase"][phrase["key"]].extend(
                    cls._remove_word_in_phrase(phrase["value"], word, phrase["key"])
                )
                tem_dict["phrase"][phrase["key"]].extend(cls._force_add_phrase(word, phrase["key"]))
            for example in cls._process_example(content, data_version):
                value = example["value"]
                tem_dict["example"][example["key"]] = value
                assist_word = value[value.find("{") + 1: value.find("}")]
                if assist_word not in answer["assist"]:
                    answer["assist"].append(assist_word)
            answer["content"].append(tem_dict)
        return answer
