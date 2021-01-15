#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython: language_level=3
# @Time  : 2020-12-25, 0025 10:10
# @Author: 佚名
# @File  : cdr_task.py
import sys
import random
import time
import threading
import cdr.request as requests
from threading import Lock
from cdr.exception import AnswerNotFoundException, AnswerWrong
from cdr.utils import settings, Answer, Course, Log, Tool
from cdr.eprogress import LineProgress, MultiProgressManager
from cdr.config import CDR_VERSION, LOG_DIR_PATH


class CDRTask:

    def __init__(self):
        self._progress = MultiProgressManager()
        self.__line_progress: LineProgress = None
        self.__progress_count = 0
        self._lock = Lock()
        self.__course_map = {}
        self._thread_count = 0

    def add_progress(self, key: str, title: str, total: int):
        tail = "%"
        if not settings.is_style_by_percent:
            tail = f"/{total}"
        self._progress.put(key, LineProgress(
            total=total, width=30, title=title, tail=tail, is_percent=settings.is_style_by_percent))

    def update_progress(self, key: str, progress: float, data: dict = None):
        self._progress.update(key, progress, data)
        Log.i(f"Key: {key}, Progress: {progress}", is_show=False)

    def finish_progress(self, key: str, msg):
        self._progress.finish(key, msg)

    def run(self):
        pass

    def do_task(self, task: dict, course_id: str, course: Course):
        pass

    def course_pretreatment(self, course: set) -> dict:
        Log.i("已开启多任务答题，预加载任务所需题库中......")
        self.__line_progress = LineProgress(total=len(course), width=50, title="题库加载进度")
        self.__line_progress.update(0)
        t_list = []
        self.__course_map = {}
        for course_id in course:
            thread = threading.Thread(target=self.__load_course, args=(course_id,))
            thread.setDaemon(True)
            thread.start()
            t_list.append(thread)
        for thread in t_list:
            thread.join()
        return self.__course_map

    def __load_course(self, course_id: str):
        self.__course_map[course_id] = Course(course_id)
        self._lock.acquire()
        self.__progress_count += 1
        self._lock.release()
        self.__line_progress.update(self.__progress_count)

    @property
    def thread_count(self):
        return self._thread_count

    @thread_count.setter
    def thread_count(self, value):
        self._lock.acquire()
        self._thread_count = value
        self._lock.release()

    @staticmethod
    def find_answer_and_finish(answer: Answer, data: dict, type_id: int) -> dict:
        is_show = not settings.is_multiple_task
        type_mode = ["StudyTask", "ClassTask"]
        content = data["stem"]["content"]
        remark = data["stem"]["remark"]
        topic_mode = data["topic_mode"]
        if topic_mode == 31:
            Log.v(f"[mode:{topic_mode}]{str(content)}", end='', is_show=is_show)
        else:
            Log.v(f"[mode:{topic_mode}]{content}({remark})", end='', is_show=is_show)
        topic_code = data["topic_code"]
        options = data["options"]
        time_spent = CDRTask.get_random_time(topic_mode, min_time=settings.min_random_time,
                                             max_time=settings.max_random_time)
        time.sleep(time_spent / 1000)
        #   根据获取到的答案与现行答案进行匹配
        skip_times = 0
        has_chance = True
        while has_chance:
            answer_id, is_skip = CDRTask.task_find_answer(answer, topic_mode, content, remark, options, skip_times)
            if is_skip:
                return CDRTask.skip_answer(topic_code, topic_mode, type_mode[type_id])
                # 答案验证
            try:
                if topic_mode == 31:
                    tem_list = answer_id
                    for i in range(0, data["answer_num"]):
                        answer_id = tem_list[i]
                        topic_code, _ = CDRTask.verify_answer(answer_id, topic_code, type_mode[type_id])
                        if not settings.is_random_time:
                            time.sleep(0.1)
                        else:
                            time.sleep(0.6)
                    has_chance = False
                else:
                    topic_code, has_chance = CDRTask.verify_answer(answer_id, topic_code, type_mode[type_id])
            except AnswerWrong as e:
                topic_code = e.topic_code
                if e.has_chance:
                    skip_times += 1
                    Log.w(e, is_show=False)
                    Log.w(f"第{skip_times}次查询答案出错，尝试跳过原答案进行搜索", is_show=False)
                    continue
                Log.v("")
                Log.w("答案错误！")
                Log.w(e)
                Log.w("请携带error-last.txt寻找GM排除适配问题")
                Log.w(f"你可以在“main{LOG_DIR_PATH[1:]}”下找到error-last.txt")
                Log.create_error_txt()
                input("等待错误检查（按下回车键即可继续执行）")
                return CDRTask.skip_answer(topic_code, topic_mode, type_mode[type_id])
            else:
                has_chance = False
                Log.v("   Done！", is_show=is_show)
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
        res = requests.post(
            url='https://gateway.vocabgo.com/Student/' + type_mode[type_id] + '/SubmitAnswerAndSave',
            json=data, headers=settings.header, timeout=settings.timeout)
        json = res.json()
        res.close()
        return json

    @staticmethod
    def task_find_answer(answer: Answer, topic_mode: int, content, remark, options: list, skip_times):
        # 答案查找
        is_skip = None
        answer_id = None
        try:
            if topic_mode == 11:
                assist_word = content[content.find("{") + 1:content.find("}")].strip()
                answer_id = answer.find_answer_by_11(assist_word, remark, options, skip_times)
            elif topic_mode == 13:
                assist_word = content[content.find("{") + 1:content.find("}")].strip()
                answer_id = answer.find_answer_by_13(assist_word, remark, options)
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
                Log.w(f"未知题型：{topic_mode}")
                Log.create_error_txt()
                input("等待错误检查（按下回车键键即可继续执行）")
        except AnswerNotFoundException as e:
            Log.v("")
            Log.w(f"{e}")
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

    @staticmethod
    def verify_answer(answer: str, topic_code: str, type_mode: str):
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
        res = requests.post(url=f'https://gateway.vocabgo.com/Student/{type_mode}/VerifyAnswer',
                            json=data, headers=settings.header, timeout=settings.timeout)
        json_data = res.json()
        res.close()
        if json_data['code'] == 10017:
            Log.w(f"\n{json_data['msg']}")
            Log.w("该限制为词达人官方行为，与作者无关\n按回车退出程序")
            input()
            sys.exit(0)
        if json_data['data']["answer_result"] == 1:
            pass
        else:
            Log.w(json_data, is_show=False)
            raise AnswerWrong(data, json_data['data']['topic_code'], json_data['data']["over_status"] != 1)
        return json_data['data']['topic_code'], json_data['data']["over_status"] != 1

    def verify_human(self, task_id: int, check_type: str = "answer"):
        self._lock.acquire()    # 防止多线程下输入混乱，用户无法分清
        data = {
            "check_type": check_type,
            "task_id": task_id,
            "timestamp": Tool.time(),
            "versions": CDR_VERSION,
        }
        res = requests.get("https://gateway.vocabgo.com/Student/Captcha/Get",
                           params=data, headers=settings.header, timeout=settings.timeout)
        json_data = res.json()
        res.close()
        if json_data["code"] == 0 and json_data["msg"] == "无需验证":
            return
        elif json_data["code"] == 0:
            Log.w(json_data["msg"])
            Log.w("词达人验证服务器暂时崩溃，请稍后再试")
            input()
        Log.i("验证码即将展示，若看不清可输入-1重新生成")
        from cdr.utils import VerificationCode
        code = VerificationCode.get_vc(json_data["data"]["original_image"], task_id)
        while code == "-1":
            data["timestamp"] = Tool.time()
            res = requests.get("https://gateway.vocabgo.com/Student/Captcha/Get",
                               params=data, headers=settings.header, timeout=settings.timeout)
            json_data = res.json()
            res.close()
            if json_data["code"] == 0 and json_data["msg"] == "无需验证":
                return
            elif json_data["code"] == 0:
                Log.w(json_data["msg"])
                Log.w("词达人验证服务器暂时崩溃，请稍后再试")
                input()
            Log.i("验证码即将展示，若看不清可输入-1重新生成")
            code = VerificationCode.get_vc(json_data["data"]["original_image"], task_id)
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
        res = requests.post("https://gateway.vocabgo.com/Student/Captcha/Check", json=data)
        # TODO 验证返回值，词达人这是上线测试一下的？怎么中途就没了？？？
        self._lock.release()

    @staticmethod
    def skip_answer(topic_code: str, topic_mode: int, type_mode: str) -> dict:
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
        res = requests.post(url=f'https://gateway.vocabgo.com/Student/{type_mode}/SkipAnswer',
                            json=data, headers=settings.header, timeout=settings.timeout)
        json = res.json()
        res.close()
        return json

    @staticmethod
    def wait_admin_choose():
        Log.w("建议携带error-last.txt反馈至负责人，由负责人排查BUG后继续")
        Log.v(f"你可以在“main{LOG_DIR_PATH[1:]}”下找到error-last.txt\n"
              "1. 以超时方式跳过本题\n2. 自主选择答案（待开发）\n"
              "#. 建议反馈此问题（该项不是选项），若要反馈此BUG，请不要选择选项1\n\n0. 结束程序")
        Log.create_error_txt()
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
