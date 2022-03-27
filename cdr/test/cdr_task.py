#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython: language_level=3
# @Time  : 2020-12-25, 0025 10:10
# @Author: 佚名
# @File  : cdr_task.py
import asyncio
import sys
import random
from cdr.aio import aiorequset as requests, Tasks
from cdr.exception import AnswerNotFoundException, AnswerWrong, LoadTaskInfoError, UnknownTypeMode
from cdr.utils import settings, Answer, Course, Log, Tool
from cdr.eprogress import LineProgress, MultiProgressManager
from cdr.config import CDR_VERSION, LOG_DIR_PATH

_logger = Log.get_logger()


class CDRTask:

    def __init__(self):
        self._progress = MultiProgressManager()
        self.__line_progress: LineProgress = None
        self.__progress_count = 0
        self.__course_map = {}
        self._tasks = Tasks(max_async=settings.multiple_chapter)
        self._lock = asyncio.Lock()
        self.task_type: str = ""

    def add_progress(self, key: str, title: str, total: int):
        tail = "%"
        if not settings.is_style_by_percent:
            tail = f"/{total}"
        self._progress.put(key, LineProgress(
            total=total, width=30, title=title, tail=tail, is_percent=settings.is_style_by_percent))

    def update_progress(self, key: str, progress: float, data: dict = None):
        self._progress.update(key, progress, data)
        _logger.i(f"Key: {key}, Progress: {progress}", is_show=False)

    def finish_progress(self, key: str, msg):
        self._progress.finish(key, msg)

    async def run(self):
        pass

    async def start_task(self):
        await asyncio.create_task(self._tasks.run())

    async def do_task(self, task: dict, course_id: str, course: Course):
        pass

    async def get_course_by_task(self, task) -> Course:
        return await Course.load_course(words=(await self.get_load_words(task)))

    async def get_load_words(self, task: dict) -> list[tuple[str, str, str]]:
        data = {
            "task_id": task["task_id"],
            "timestamp": Tool.time(),
            "versions": CDR_VERSION
        }
        if task.get("release_id"):
            data["release_id"] = task["release_id"]
        else:
            data["course_id"] = task["course_id"]
            data["list_id"] = task["list_id"]
        await asyncio.sleep(0.3)
        res = await requests.get(f"https://gateway.vocabgo.com/Student/{self.task_type}/Info",
                                 params=data, headers=settings.header, timeout=settings.timeout)
        json_data = (await res.json())
        res.close()
        if json_data["code"] != 1:
            raise LoadTaskInfoError(json_data["msg"])
        task["task_id"] = json_data["data"]["task_id"]
        if task["task_id"] == -1:
            data["task_id"] = -1
            data["timestamp"] = Tool.time()
            res = await requests.get(f"https://gateway.vocabgo.com/Student/{self.task_type}/Info",
                                     params=data, headers=settings.header, timeout=settings.timeout)
            json_data = (await res.json())
            res.close()
        if json_data["code"] != 1:
            raise LoadTaskInfoError(json_data["msg"])
        json_data = json_data["data"]["word_list"]
        word_list = []
        for word_info in json_data:
            word_list.append((word_info["course_id"], word_info["list_id"], word_info["word"]))
        return word_list

    async def find_answer_and_finish(self, answer: Answer, data: dict, task_id: int) -> dict:
        is_show = not settings.is_multiple_chapter
        content = data["stem"]["content"]
        remark = data["stem"]["remark"]
        topic_mode = data["topic_mode"]
        if topic_mode == 31:
            _logger.v(f"[mode:{topic_mode}]{str(content)}", end='', is_show=is_show)
        else:
            _logger.v(f"[mode:{topic_mode}]{content}({remark})", end='', is_show=is_show)
        topic_code = data["topic_code"]
        options = data["options"]
        #   根据获取到的答案与现行答案进行匹配
        skip_times = 0
        has_chance = True
        while has_chance:
            answer_id, is_skip = CDRTask.task_find_answer(answer, topic_mode, content, remark, options, skip_times)
            if is_skip:
                return await CDRTask.skip_answer(topic_code, topic_mode, self.task_type)
                # 答案验证
            try:
                if topic_mode == 31:
                    tem_list = answer_id
                    for i in range(0, data["answer_num"]):
                        answer_id = tem_list[i]
                        topic_code, _ = await self.verify_answer(answer_id, topic_code, task_id)
                        if not settings.is_random_time:
                            await asyncio.sleep(0.1)
                        else:
                            await asyncio.sleep(random.randint(3 * 1000, 5 * 1000) / 1000)
                    has_chance = False
                else:
                    topic_code, has_chance = await self.verify_answer(answer_id, topic_code, task_id)
            except AnswerWrong as e:
                topic_code = e.topic_code
                if e.has_chance:
                    skip_times += 1
                    _logger.w(e, is_show=False)
                    _logger.w(f"第{skip_times}次查询答案出错，尝试跳过原答案进行搜索", is_show=False)
                    continue
                _logger.v("")
                _logger.w("答案错误！")
                _logger.w(e)
                _logger.w("请携带error-last.txt寻找GM排除适配问题")
                _logger.w(f"你可以在“main{LOG_DIR_PATH[1:]}”下找到error-last.txt")
                _logger.create_error_txt()
                input("等待错误检查（按下回车键即可继续执行）")
                return await CDRTask.skip_answer(topic_code, topic_mode, self.task_type)
            else:
                has_chance = False
                _logger.v("   Done！", is_show=is_show)

        time_spent = CDRTask.get_random_time(topic_mode, min_time=settings.min_random_time,
                                             max_time=settings.max_random_time)
        await asyncio.sleep(time_spent / 1000)
        timestamp = Tool.time()
        sign = Tool.md5(f"time_spent={time_spent}&timestamp={timestamp}&topic_code={topic_code}"
                        + f"&versions={CDR_VERSION}ajfajfamsnfaflfasakljdlalkflak")
        data = {
            "topic_code": topic_code,
            "time_spent": time_spent,
            "timestamp": timestamp,
            "versions": CDR_VERSION,
            "sign": sign
        }
        res = await requests.post(
            url=f'https://gateway.vocabgo.com/Student/{self.task_type}/SubmitAnswerAndSave',
            json=data, headers=settings.header, timeout=settings.timeout)
        json_data = await res.json()
        res.close()
        if json_data["code"] == 21006:
            await self.verify_human(task_id)
            data["timestamp"] = Tool.time()
            res = await requests.post(
                url=f'https://gateway.vocabgo.com/Student/{self.task_type}/SubmitAnswerAndSave',
                json=data, headers=settings.header, timeout=settings.timeout)
            json_data = await res.json()
            res.close()
        #  请求模拟
        # requests.post(
        #     url='https://gateway.vocabgo.com/Student/Course/GetStudyWordInfo',
        #     json=data, headers=settings.header, timeout=settings.timeout).close()
        return json_data

    @staticmethod
    def task_find_answer(answer: Answer, topic_mode: int, content, remark, options: list, skip_times):
        # 答案查找
        is_skip = None
        answer_id = None
        try:
            if topic_mode == 11:
                answer_id = answer.find_answer_by_11(content, remark, options, skip_times)
            elif topic_mode == 13:
                answer_id = answer.find_answer_by_13(content, remark, options)
            elif topic_mode == 15 or topic_mode == 16 \
                    or topic_mode == 21 or topic_mode == 22:
                answer_id = answer.find_answer_by_15(content.strip(), options)
            elif topic_mode == 17 or topic_mode == 18:
                answer_id = answer.find_answer_by_17(content, options)
            elif topic_mode == 31:
                answer_id = answer.find_answer_by_31(remark, options)
            elif topic_mode == 32:
                answer_id = answer.find_answer_by_32(remark, options,
                                                     Tool.count_character_in_str("_", content), skip_times)
            elif topic_mode == 41 or topic_mode == 42:
                answer_id = answer.find_answer_by_41(content, remark, options)
            elif topic_mode == 43 or topic_mode == 44:
                answer_id = answer.find_answer_by_43(content, remark, options)
            elif topic_mode == 51 or topic_mode == 52:
                answer_id = answer.find_answer_by_51(content, remark, skip_times)
            elif topic_mode == 53 or topic_mode == 54:
                answer_id = answer.find_answer_by_53(content, remark)
            else:
                raise UnknownTypeMode(topic_mode)
        except AnswerNotFoundException as e:
            _logger.v("")
            _logger.w(f"{e}")
            CDRTask.wait_admin_choose()
            is_skip = True
        return answer_id, is_skip

    @staticmethod
    def get_random_time(topic_mode, min_time=5, max_time=0, is_max=False):
        #   不同题型所容许的最大提交时间（单位：秒）
        max_time_list = {
            "11": 20, "13": 35, "15": 15, "16": 15, "17": 10, "18": 10,
            "21": 15, "22": 15, "31": 25, "32": 20, "41": 25, "42": 25,
            "43": 30, "44": 30, "51": 25, "52": 25, "53": 35, "54": 35
        }
        if is_max:
            return max_time_list[str(topic_mode)] * 1000
        if max_time > max_time_list[str(topic_mode)]:
            max_time = max_time_list[str(topic_mode)]
        if min_time >= max_time:
            min_time = max_time - 0.01
        if min_time <= 0:
            min_time = 5
            max_time = 10
        if max_time != 0 and settings.is_random_time:
            return random.randint(min_time * 1000, max_time * 1000)
        return 100

    @staticmethod
    def get_random_score(is_open=False):
        base_score = settings.base_score
        offset_score = settings.offset_score
        if not is_open:
            return 100
        #   保证随机一个小数点
        min_score = (base_score - offset_score) * 10
        max_score = (base_score + offset_score) * 10
        #   修正参数
        if min_score < 600:
            min_score = 600
        if max_score > 1000:
            max_score = 1000
        return random.randint(min_score, max_score) / 10.0

    async def verify_answer(self, answer: str, topic_code: str, task_id: int):
        timestamp = Tool.time()
        sign = Tool.md5(f"answer={answer}&timestamp={timestamp}&topic_code={topic_code}"
                        + f"&versions={CDR_VERSION}ajfajfamsnfaflfasakljdlalkflak")
        data = {
            "answer": answer,
            "topic_code": topic_code,
            "timestamp": timestamp,
            "versions": CDR_VERSION,
            "sign": sign
        }
        res = await requests.post(url=f'https://gateway.vocabgo.com/Student/{self.task_type}/VerifyAnswer',
                                  json=data, headers=settings.header, timeout=settings.timeout)
        json_data = await res.json()
        res.close()
        if json_data["code"] == 21006:
            await self.verify_human(task_id)
            data["timestamp"] = Tool.time()
            res = await requests.post(url=f'https://gateway.vocabgo.com/Student/{self.task_type}/VerifyAnswer',
                                      json=data, headers=settings.header, params=data, timeout=settings.timeout)
            json_data = await res.json()
            res.close()
        if json_data['code'] == 10017:
            _logger.w(f"\n{json_data['msg']}")
            _logger.w("该限制为词达人官方行为，与作者无关\n按回车退出程序")
            input()
            sys.exit(0)
        if json_data['data']["answer_result"] == 1:
            pass
        else:
            _logger.w(json_data, is_show=False)
            raise AnswerWrong(data, json_data['data']['topic_code'], json_data['data']["over_status"] != 1)
        return json_data['data']['topic_code'], json_data['data']["over_status"] != 1

    async def verify_human(self, task_id: int, check_type: str = "answer"):
        async with self._lock:
            data = {
                "check_type": check_type,
                "task_id": task_id,
                "versions": CDR_VERSION,
            }
            fail_times = 0
            while True:
                fail_times = fail_times + 1
                data["timestamp"] = Tool.time()
                res = await requests.get("https://gateway.vocabgo.com/Student/Captcha/Get",
                                         params=data, headers=settings.header, timeout=settings.timeout)
                json_data = await res.json()
                res.close()
                ""
                if json_data["code"] == 0 and json_data["msg"] == "无需验证":
                    return
                elif json_data["code"] == 0:
                    if json_data["msg"].find("频繁") != -1:
                        _logger.w(f"疑似词达人验证码服务器限制\n词达人返回信息：{json_data['msg']}\n")
                    else:
                        _logger.w(json_data["msg"])
                        _logger.w("词达人验证服务器暂时崩溃，请稍后再试")
                    _logger.v("按回车尝试重新请求验证码")
                    input()
                    fail_times = fail_times - 1
                    continue
                _logger.i(json_data, is_show=False)
                from cdr.utils import VerificationCode
                code = await VerificationCode.get_vc(json_data["data"]["original_image"], task_id, fail_times)
                while code == "-1":
                    res = await requests.get("https://gateway.vocabgo.com/Student/Captcha/Get",
                                             params=data, headers=settings.header, timeout=settings.timeout)
                    json_data = await res.json()
                    res.close()
                    if json_data["code"] == 0 and json_data["msg"] == "无需验证":
                        return
                    elif json_data["code"] == 0:
                        _logger.v("")
                        _logger.w(json_data["msg"])
                        _logger.w("词达人验证服务器暂时崩溃，请稍后再试")
                        input("按回车重新尝试生成验证码")
                        continue
                    code = await VerificationCode.get_vc(json_data["data"]["original_image"], task_id, fail_times)
                timestamp = Tool.time()
                sign = Tool.md5(f"captcha_code={code}&task_id={task_id}&timestamp={timestamp}&versions={CDR_VERSION}"
                                "ajfajfamsnfaflfasakljdlalkflak")
                data = {
                    "captcha_code": code,
                    "sign": sign,
                    "task_id": task_id,
                    "timestamp": timestamp,
                    "versions": CDR_VERSION
                }
                res = await requests.post("https://gateway.vocabgo.com/Student/Captcha/Check",
                                          json=data, headers=settings.header)
                flag = (await res.json())["code"]
                res.close()
                if flag != 1:
                    _logger.i("验证码核验错误，将重新生成验证码")

    @staticmethod
    async def skip_answer(topic_code: str, topic_mode: int, type_mode: str) -> dict:
        time_spent = CDRTask.get_random_time(topic_mode, is_max=True)
        timestamp = Tool.time()
        sign = Tool.md5(f"time_spent={time_spent}&timestamp={timestamp}&topic_code={topic_code}"
                        + f"&versions={CDR_VERSION}ajfajfamsnfaflfasakljdlalkflak")
        data = {
            "topic_code": topic_code,
            "time_spent": time_spent,
            "timestamp": timestamp,
            "versions": CDR_VERSION,
            "sign": sign
        }
        res = await requests.post(url=f'https://gateway.vocabgo.com/Student/{type_mode}/SkipAnswer',
                                  json=data, headers=settings.header, timeout=settings.timeout)
        json = await res.json()
        res.close()
        return json

    @staticmethod
    def wait_admin_choose():
        _logger.w("建议携带error-last.txt反馈至负责人，由负责人排查BUG后继续")
        _logger.v(f"你可以在“main{LOG_DIR_PATH[1:]}”下找到error-last.txt\n"
                  "1. 以超时方式跳过本题\n2. 自主选择答案（待开发）\n"
                  "#. 建议反馈此问题（该项不是选项），若要反馈此BUG，请不要选择选项1\n\n0. 结束程序")
        _logger.create_error_txt()
        code_type = input("\n请输入指令：")
        if CDRTask.check_input_data(code_type, 1) and code_type == "1":
            return
        else:
            sys.exit(0)

    @staticmethod
    def check_input_data(s, num):
        try:
            int(s)
        except ValueError:
            return False
        else:
            return num >= int(s) >= 0
