#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2020-12-19, 0019 21:18
# @Author: 佚名
# @File  : course.py
import json
import re
import requests
import os
import threading
from threading import Lock
from .setting import Settings
from .log import Log
from .tool import Tool
from cdr.config import CDR_VERSION, DATA_DIR_PATH

_settings: Settings = Settings()


class Course:
    DATA_VERSION = 3

    def __init__(self, course_id):
        self.id = course_id
        self.data = {}
        if self._load_local_answer():
            return
        Log.i("从网络装载题库中......(10s-30s)")
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
        self._lock = Lock()
        self.is_success = True
        #   获取课程所有列表
        res = requests.get("https://gateway.vocabgo.com/Teacher/Course/UnitList?course_id={}&timestamp={}&versions={}"
                           .format(course_id, Tool.time(), CDR_VERSION),
                           headers=self._headers, timeout=_settings.timeout)
        m_array = res.json()["data"]["course_list_info_list"]
        res.close()
        t_list = []
        self._fail_list = []
        for m_list in m_array:
            #   根据课程id及列表id获取所有单词
            #   多线程加载单词，否则时间过长
            thread = threading.Thread(target=self._use_thread_load_word, args=(course_id, m_list["list_id"]))
            thread.setDaemon(True)
            thread.start()
            t_list.append(thread)
        for thread in t_list:
            thread.join()
        t_list.clear()
        del t_list
        m_array.clear()
        del m_array
        self.is_success = True
        for list_id in self._fail_list:
            self._use_thread_load_word(course_id, list_id, is_second=True)
        if self.is_success:
            with open(DATA_DIR_PATH + self.id, mode='w', encoding='utf-8') as answer:
                tem = {
                    "courseId": course_id,
                    "data": self.data,
                    "version": Course.DATA_VERSION
                }
                answer.write(json.dumps(tem))
                answer.close()

    def _load_local_answer(self) -> bool:
        if not os.path.exists(DATA_DIR_PATH + self.id):
            return False
        with open(DATA_DIR_PATH + self.id, mode='r', encoding='utf-8') as answer:
            data = json.loads(answer.read())
            answer.close()
            if data["version"] < Course.DATA_VERSION:
                return False
            Log.i("复用上次本地缓存题库")
            self.data = data["data"]
            return True

    def _use_thread_load_word(self, course_id: str, list_id: str, is_second: bool = False):
        global _settings
        timeout = _settings.timeout
        base_url = "https://gateway.vocabgo.com/Teacher/Course/UnitWordList?config_id=-1&course_id={}&list_id={}"\
            .format(course_id, list_id)
        res = requests.get(f"{base_url}&timestamp={Tool.time()}&versions={CDR_VERSION}",
                           headers=self._headers, timeout=timeout)
        m_array_1 = res.json()["data"]["word_list"]
        res.close()
        for word in m_array_1:
            answer = None
            try:
                answer = self.get_detail_by_word(course_id, list_id, word)
            except Exception as e:
                if not is_second:
                    Log.w(f"警告！单词：{word}({course_id}/{list_id})加载失败，稍后软件将会尝试二次加载")
                else:
                    Log.w(f"警告！单词：{word}({course_id}/{list_id})二次加载失败，本次不会缓存本地词库")
                self.is_success = False
                self._lock.acquire()
                self._fail_list.append(list_id)
                self._lock.release()
                continue
            else:
                if is_second:
                    Log.d(f"单词：{word}二次加载成功！")
            self._lock.acquire()
            if self.data.get(word) is None:
                self.data[word] = answer
            else:
                self.data[word]["content"].extend(answer["content"])
                self.data[word]["assist"].extend(answer["assist"])
            self._lock.release()
        m_array_1.clear()
        del m_array_1

    def find_detail_by_word(self, word):
        return self.data.get(word) or self.data.get(word.lower())

    def find_detail_by_assist_word(self, word):
        tem_list = []
        for key in self.data:
            if word in self.data[key]["assist"] or word.lower() in self.data[key]["assist"]:
                tem_list.append(self.data[key])
        return tem_list

    @staticmethod
    def get_detail_by_word(course_id, list_id, word):
        global _settings
        timeout = _settings.timeout
        data = {
            "course_id": course_id,
            "list_id": list_id,
            "word": word
         }
        res = requests.get(
            url='https://gateway.vocabgo.com/Student/Course/StudyWordInfo',
            params=data,
            headers=_settings.header,
            timeout=timeout)
        data = res.json()["data"]
        res.close()
        answer = {
            "content": [],
            "assist": []
        }
        count = 0
        pattern = re.compile(r"([0-9A-Za-z\.\s\(\)\{\}'/&‘’,（）…-]*)?\s(.*)")
        is_more = re.compile(r"(.*…)\s(…[^a-zA-Z]*)")
        for i, o in enumerate(data["options"]):
            count = count + 1
            content = o["content"]
            answer["content"].append({})
            #   统一词义格式：1.多空格去除为1空格 2.删除中文括号中的附加内容
            c_str = ' '.join(content["mean"].split())
            while c_str.find("（") != -1:
                c_str = c_str[:c_str.find("（")] + c_str[c_str.find("）") + 1:]
            answer["content"][i]["mean"] = ' '.join(c_str.split())
            del c_str
            answer["content"][i]["usage"] = {}
            answer["content"][i]["example"] = {}
            #   辅助单词列表，存放当前单词例句中的不同时态
            #   处理答案
            for j in content["usage"]:
                matcher = None
                if is_more.match(j) is None:
                    matcher = pattern.match(j)
                else:
                    matcher = re.match(r"([0-9A-Za-z\.\s\(\)\{\}'/&‘’,（）…-]*)?\s(….*)", j)
                if matcher is None:
                    print(j)
                tem_list = matcher.group(1).replace('{', '').replace('}', '') \
                    .replace('.', ' ').replace("…", " ").replace("-", " ").replace(",", " ")
                #   处理因清理"..."而造成的多余空格
                tem_list = " ".join(tem_list.split()).split(" ")
                tem_str = matcher.group(2)
                #   因不同短语可能具有相同的翻译，需做额外处理
                if answer["content"][i]["usage"].get(tem_str) is None:
                    answer["content"][i]["usage"][tem_str] = []
                answer["content"][i]["usage"][tem_str].append(tem_list)
            for j in content["example"]:
                answer["content"][i]["example"][j["sen_mean_cn"]] = j["sen_content"]
                tem_word = j["sen_content"][j["sen_content"].find("{") + 1:j["sen_content"].find("}")]
                if tem_word not in answer["assist"]:
                    answer["assist"].append(tem_word)
        return answer

