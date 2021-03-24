#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-27, 0027 13:10
# @Author: 佚名
# @File  : class_task.py
import json
import gc
import re
import time
import cdr.request as requests

from .cdr_task import CDRTask
from cdr.utils import settings, Answer, Course, Log, Tool
from cdr.thread import CustomThread
from cdr.config import CDR_VERSION, CONFIG_DIR_PATH
from cdr.exception import NoPermission


class ClassTask(CDRTask):

    def run(self):
        task_type_list = ["未知", "学习", "测试"]
        over_status_list = ["未知", "未开始", "进行中", "已过期"]
        time_type_list = ["未知", "开始", "截止", "截止"]
        task_list = ClassTask.get_task_list()
        #   任务选择
        if len(task_list) == 0:
            input("全部任务已完成，无可做任务\n按回车键返回上一级")
            return
        Tool.cls()
        while True:
            Log.v("请输入序号去选择要做的任务：\n")
            for i, task in enumerate(task_list):
                time_stamp = task['start_time']
                if task['over_status'] != 1:
                    time_stamp += task['over_time']
                time_stamp /= 1000
                Log.i(time_stamp, is_show=False)
                format_time = time.strftime("%m{m}%d{d} %H:%M:%S", time.localtime(time_stamp)).format(m="月", d="号")
                Log.i(format_time, is_show=False)
                Log.v(f"{i + 1:2d}. [{task_type_list[task['task_type']]}]"
                      + f"[{over_status_list[task['over_status']]}] {task['task_name']:20s}"
                      + f"（{task['score']:2.1f}分） {format_time}{time_type_list[task['over_status']]}")
            Log.v("\n#.  以空格分割可一次性选择多个任务")
            Log.v(f"#.  你可以在“main{CONFIG_DIR_PATH[1:]}config.txt文件”中修改配置项以控分/修改做题时间间隔等")
            Log.v("\n\n0.  选择全部任务\n\n请输入序号：", end="")
            choose = ' '.join(input("").split()).split(" ")
            Log.v(choose, is_show=False)
            task_choose_list = []
            tem_flag = True
            if CDRTask.check_input_data(choose[0], 0):
                task_choose_list = task_list
            else:
                for c in choose:
                    if not CDRTask.check_input_data(c, len(task_list)):
                        tem_flag = False
                        Tool.cls()
                        Log.i("输入格式有误！\n")
                        break
                    task_choose_list.append(task_list[int(c) - 1])
            if tem_flag:
                break
        course_set = set()
        if settings.is_multiple_task:
            # 课程单词预处理加载
            for task in task_choose_list:
                course_id = task.get("course_id") or re.match(r'.*/(.*)\.jpg', task["course_img_url"]).group(1)
                course_set.add(course_id)
            course_map = self.course_pretreatment(course_set)
            Tool.cls()
            t_list = []
            for task in task_choose_list:
                self.thread_count += 1
                course_id = task.get("course_id") or re.match(r'.*/(.*)\.jpg', task["course_img_url"]).group(1)
                thread = CustomThread(target=self.do_task, args=(task, course_id, course_map[course_id]))
                thread.setDaemon(True)
                thread.start()
                t_list.append(thread)
                if self.thread_count >= settings.multiple_task:
                    for thread in t_list:
                        thread.join()
                    self._progress.clear()
                    t_list = []
                    self.thread_count = 0
            # 防止线程数量不足而独立于主线程完成任务
            self._progress.clear()
            for thread in t_list:
                thread.join()
        else:
            for task in task_choose_list:
                # 未过期任务
                #   over_status为任务标识，1：未开始 2：进行中 3：已过期
                #   task_id仅作为辅助标识，若任务是多单元混合，其为-1，若是单独，则其为对应课程号
                #   task_type为任务类型标识（未证实） 1：学习任务 2：测试任务
                course_id = task.get("course_id") or re.match(r'.*/(.*)\.jpg', task["course_img_url"]).group(1)
                self.do_task(task, course_id, None)
                # Log.v("")
        Log.i("本次全部任务已完成！")
        input("按回车键返回上一级")

    def do_task(self, task, course_id, course):
        time_out = settings.timeout
        is_random_score = settings.is_random_score
        is_show = not settings.is_multiple_task
        if task['over_status'] == 2:
            task_id = task["task_id"]
            task_type = task["task_type"]
            release_id = task["release_id"]
            now_score = CDRTask.get_random_score(is_open=is_random_score)
            Log.i("course_id:" + course_id, is_show=False)
            Log.i("开始做【" + task["task_name"] + "】，目标分数：" + str(now_score), is_show=is_show)
            answer = Answer(course) if course else Answer(Course(course_id))
            Log.i("题库装载完毕！", is_show=is_show)
            count = 0
            while True:
                count += 1
                if count > 3:
                    Log.w("相同任务重复答题次数过多，疑似存在无法找到答案的题目，自动跳过本任务", is_show=is_show)
                    break
                Log.i("模拟加载流程", is_show=is_show)
                if task_type == 1:
                    #   模拟加载流程
                    Log.i("班级-学习任务", is_show=is_show)
                    # 处理taskId为-1的情况
                    task_id = ClassTask.get_task_id(task_id, release_id)
                    time.sleep(1)
                data = {
                    "task_id": task_id,
                    "task_type": task_type,
                    "release_id": release_id,
                    "timestamp": Tool.time(),
                    "versions": CDR_VERSION
                }
                res = requests.get(url='https://gateway.vocabgo.com/Student/ClassTask/StartAnswer',
                                   headers=settings.header, params=data, timeout=time_out)
                json_data = res.json()
                res.close()
                if task_type == 1:
                    #   判断是否需要选词
                    try:
                        if json_data["code"] == 20001 and ClassTask.choose_word(course_id, task_id, task_type):
                            break
                    except NoPermission as e:
                        Log.w(e)
                        Log.w("疑似未开通VIP课程，请自行购买VIP课程或反馈至学校购买后再进行答题操作")
                        break
                    # 开始任务包
                    timestamp = Tool.time()
                    data = {
                        "task_id": task_id,
                        "task_type": task_type,
                        "release_id": release_id,
                        "timestamp": timestamp,
                        "versions": CDR_VERSION
                    }
                    res = requests.get(url='https://gateway.vocabgo.com/Student/ClassTask/StartAnswer',
                                       headers=settings.header, params=data, timeout=time_out)
                    json_data = res.json()
                    res.close()
                    if json_data["code"] == 21006:
                        self.verify_human(task_id)
                        data["timestamp"] = Tool.time()
                        res = requests.get(url='https://gateway.vocabgo.com/Student/ClassTask/StartAnswer',
                                           headers=settings.header, params=data, timeout=time_out)
                        json_data = res.json()
                        res.close()
                    time.sleep(1)
                    if json_data["code"] == 0 and json_data["msg"] is not None \
                            and json_data["msg"].find("返回首页") != -1:
                        Log.i("任务信息加载失败，返回上一级重选任务即可", is_show=is_show)
                        input("按回车返回上一级")
                        return
                    #   判断是否跳过学习阶段
                    Log.i(json_data, is_show=False)
                    if json_data["data"]["topic_mode"] == 0:
                        json_data = ClassTask.skip_learn_task(json_data["data"]["topic_code"])
                        Log.i("已跳过学习阶段", is_show=is_show)
                else:
                    Log.i("班级-测试任务", is_show=is_show)
                    # 开始任务包
                    time.sleep(1)
                Log.i("开始答题\n", is_show=is_show)
                if json_data["code"] == 0:
                    Log.i(json_data["msg"], is_show=is_show)
                    return
                if settings.is_multiple_task:
                    Log.i(json_data, is_show=False)
                    self.add_progress(str(release_id), task['task_name'], json_data['data']['topic_total'])
                    self.update_progress(str(release_id), 0)
                # 提交做题
                #   code=20004时代表当前题目已做完，测试任务完成标志
                #   code=20001需要选词，学习任务完成标志
                while json_data["code"] != 20004 and json_data["code"] != 20001 and \
                        json_data["data"]["topic_done_num"] <= json_data["data"]["topic_total"]:
                    if settings.is_multiple_task:
                        self.update_progress(str(release_id), json_data["data"]["topic_done_num"])
                    json_data = self.do_question(answer, json_data, release_id, now_score, task_id)
                if is_show:
                    Log.i(f"【{task['task_name']}】已完成。分数：{ClassTask.get_class_task_score(release_id)}")
                else:
                    self.finish_progress(str(release_id), f"分数：{ClassTask.get_class_task_score(release_id)}")
                if json_data["code"] == 20004:
                    break
                if now_score <= ClassTask.get_class_task_score(release_id):
                    break
        else:
            Log.i(f"该【{task['task_name']}】任务未开始")
        self.thread_count -= 1

    @staticmethod
    def get_task_list():
        time_out = settings.timeout
        task_type_list = ["未知", "学习", "测试"]
        over_status_list = ["未知", "未开始", "进行中", "已过期"]
        res = requests.get(
            url=f'https://gateway.vocabgo.com/Student/ClassTask/List?page_count=1&page_size=20&timestamp={Tool.time()}'
                + f'&versions={CDR_VERSION}', headers=settings.header, timeout=time_out
        )
        task_list = res.json()['data']['task_list']
        Log.i(task_list, is_show=False)
        res.close()
        tem_list = []
        count = 2
        flag = True
        while flag:
            for i in task_list:
                #   排除已过期任务及已完成任务
                Log.i(i, is_show=False)
                Log.i(f"[{task_type_list[i['task_type']]}][{over_status_list[i['over_status']]}] "
                      f"{i['task_name']} （{i['score']}分）", is_show=False)
                if i['over_status'] != 3 and (i["task_type"] == 1 and i['score'] != 100 or i['progress'] != 100):
                    tem_list.append(i)
            if len(task_list) != 20:
                flag = False
            else:
                # 模拟预请求
                requests.options(
                    url=f'https://gateway.vocabgo.com/Student/ClassTask/List?page_count={count:d}&page_size=20'
                    f'&timestamp={Tool.time()}&versions={CDR_VERSION}', headers=settings.header, timeout=time_out
                ).close()
                response = requests.get(
                    url=f'https://gateway.vocabgo.com/Student/ClassTask/List?page_count={count:d}&page_size=20'
                    f'&timestamp={Tool.time()}&versions={CDR_VERSION}', headers=settings.header, timeout=time_out
                )
                task_list = response.json()['data']['task_list']
                response.close()
                count += 1
        return tem_list

    @staticmethod
    def get_task_id(task_id: int, release_id: int) -> int:
        count = 0
        while task_id == -1 and count < 5:
            res = requests.get(f"https://gateway.vocabgo.com/Student/ClassTask/Info?task_id={task_id:d}"
                               f"&release_id={release_id:d}&timestamp={Tool.time()}&versions={CDR_VERSION}",
                               headers=settings.header, timeout=settings.timeout)
            json_data = res.json()
            res.close()
            if json_data["code"] == 1:
                task_id = json_data["data"]["task_id"]
            Log.i(f"task_id:{task_id:d},count:{count:d}", is_show=False)
            count = count + 1
        return task_id

    @staticmethod
    def choose_word(course_id: str, task_id: int, task_type: int) -> bool:
        is_show = not settings.is_multiple_task
        time_out = settings.timeout
        Log.i("需要选词", is_show=is_show)
        res = requests.get(
            url=f'https://gateway.vocabgo.com/Student/ClassTask/ChoseWordList?task_id={task_id}'
            f'&task_type={task_type}&timestamp={Tool.time()}&versions={CDR_VERSION}',
            headers=settings.header, timeout=time_out)
        json_data = res.json()
        res.close()
        if json_data["code"] == 0 and json_data["msg"].find("开通权限") != -1:
            raise NoPermission(json_data["msg"])
        word_map = {}
        for word in json_data['data']['word_list']:
            if word['score'] != 10:
                tem_str = course_id + ':' + word["list_id"]
                if word_map.get(tem_str) is None:
                    word_map[tem_str] = []
                word_map[tem_str].append(word['word'])
        if len(word_map) == 0:
            Log.i("当前学习任务已完成", is_show=is_show)
            return True
        Log.i(word_map, is_show=False)
        tem_i = 0
        tem_len = 0
        for k in word_map:
            tem_len += len(word_map[k])
        while tem_len < 5:
            tem_o = json_data['data']['word_list'][tem_i]
            tem_str = course_id + ':' + tem_o["list_id"]
            if tem_o['word'] not in word_map[tem_str]:
                if word_map.get(tem_str) is None:
                    word_map[tem_str] = []
                word_map[tem_str].append(tem_o['word'])
                Log.i(f"单词复选：{tem_o['word']}", is_show=False)
            tem_i = tem_i + 1

            tem_len = 0
            for k in word_map:
                tem_len += len(word_map[k])
        Log.i(word_map, is_show=False)
        timestamp = Tool.time()
        sign = Tool.md5(f'task_id={task_id}&timestamp={timestamp}&versions={CDR_VERSION}&word_map='
                        + json.dumps(word_map, separators=(',', ':')).replace("'", '"')
                        + 'ajfajfamsnfaflfasakljdlalkflak')
        data = {
            "task_id": task_id,
            "word_map": word_map,
            "timestamp": timestamp,
            "versions": CDR_VERSION,
            "sign": sign
        }
        res = requests.post(
            url='https://gateway.vocabgo.com/Student/ClassTask/SubmitChoseWord',
            headers=settings.header, json=data, timeout=time_out)
        Log.i(res.json(), is_show=False)
        res.close()
        Log.i("选词完毕！", is_show=is_show)
        return False

    @staticmethod
    def skip_learn_task(topic_code: str):
        is_show = not settings.is_multiple_task
        #   模拟加载流程
        Log.i("正在跳过学习任务的学习阶段", is_show=is_show)
        timestamp = Tool.time()
        time_spent = 0
        sign = Tool.md5(f"time_spent={time_spent}&timestamp={timestamp}&topic_code={topic_code}"
                        f"&versions={CDR_VERSION}ajfajfamsnfaflfasakljdlalkflak")
        data = {
            "topic_code": topic_code,
            "time_spent": time_spent,
            "timestamp": timestamp,
            "versions": CDR_VERSION,
            "sign": sign
        }
        res = requests.post(
            url='https://gateway.vocabgo.com/Student/ClassTask/SubmitAnswerAndSave',
            json=data, headers=settings.header, timeout=settings.timeout)
        json_data = res.json()
        res.close()
        time.sleep(1)
        #   流程模拟结束
        timestamp = Tool.time()
        sign = Tool.md5(f"timestamp={timestamp}&topic_code={json_data['data']['topic_code']}"
                        f"&versions={CDR_VERSION}ajfajfamsnfaflfasakljdlalkflak")
        data = {
            "topic_code": json_data['data']['topic_code'],
            "timestamp": timestamp,
            "versions": CDR_VERSION,
            "sign": sign
        }
        res = requests.post(
            url='https://gateway.vocabgo.com/Student/ClassTask/SkipNowTopicMode',
            json=data, headers=settings.header, timeout=settings.timeout)
        json_data = res.json()
        res.close()
        return json_data

    @staticmethod
    def get_class_task_score(release_id):
        requests.options(
            url='https://gateway.vocabgo.com/Student/ClassTask/List?page_count=1&page_size=10&timestamp='
                + f'{Tool.time()}&versions={CDR_VERSION}', headers=settings.header, timeout=settings.timeout).close()
        res = requests.get(
            url='https://gateway.vocabgo.com/Student/ClassTask/List?page_count=1&page_size=100&timestamp='
                + f'{Tool.time()}&versions={CDR_VERSION}', headers=settings.header, timeout=settings.timeout)
        json_data = res.json()
        res.close()
        for task in json_data['data']['task_list']:
            if task["release_id"] == release_id:
                return task["score"]
        return 0

    def do_question(self, answer: Answer, json_data: dict, release_id, now_score, task_id: int) -> dict:
        is_show = not settings.is_multiple_task
        Log.i(str(json_data["data"]["topic_done_num"])
              + "/" + str(json_data["data"]["topic_total"]) + ".", end='', is_show=is_show)
        if now_score != 100 and 100.0 * json_data["data"]["topic_done_num"] / \
                json_data["data"]["topic_total"] + 5 >= now_score:
            if not settings.is_random_time:
                time.sleep(0.1)
            else:
                time.sleep(2)
            if ClassTask.get_class_task_score(release_id) >= now_score:
                Log.i(f"[mode:{json_data['data']['topic_mode']}]{json_data['data']['stem']['content']}"
                      + "   已达本次既定分数，超时本题！", is_show=is_show)
                json_data = CDRTask.skip_answer(json_data["data"]["topic_code"],
                                                json_data["data"]["topic_mode"],
                                                "ClassTask")
            else:
                json_data = self.find_answer_and_finish(answer, json_data["data"], 1, task_id)
        else:
            json_data = self.find_answer_and_finish(answer, json_data["data"], 1, task_id)
        #   每10道题清理一次gc
        if json_data.get("data") is None:
            Log.e(json_data, is_show=False)
        if json_data["code"] == 1 and json_data["data"]["topic_done_num"] % 10 == 0:
            gc.collect()
            gc.set_debug(gc.DEBUG_UNCOLLECTABLE)
        return json_data
