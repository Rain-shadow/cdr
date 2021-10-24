#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-27, 0027 13:10
# @Author: 佚名
# @File  : class_task.py
import asyncio
import json
import gc
import re
from cdr.aio import aiorequset as requests

from .cdr_task import CDRTask
from cdr.utils import settings, Answer, Course, Log, Tool
from cdr.config import CDR_VERSION, CONFIG_DIR_PATH
from cdr.exception import NoPermission

_logger = Log.get_logger()


class ClassTask(CDRTask):

    async def run(self):
        self.task_type = "ClassTask"
        task_type_list = ["未知", "学习", "测试"]
        over_status_list = ["未知", "未开始", "进行中", "已过期"]
        time_type_list = ["未知", "开始", "截止", "截止"]
        task_list = await ClassTask.get_task_list()
        #   任务选择
        if len(task_list) == 0:
            _logger.i("全部任务已完成，无可做任务")
            input("按回车键返回上一级")
            return
        Tool.cls()
        while True:
            _logger.v("请输入序号去选择要做的任务：\n")
            for i, task in enumerate(task_list):
                time_stamp = task['start_time']
                if task['over_status'] != 1:
                    time_stamp += task['over_time']
                time_stamp /= 1000
                _logger.i(time_stamp, is_show=False)
                import time
                format_time = time.strftime("%m{m}%d{d} %H:%M:%S", time.localtime(time_stamp)).format(m="月", d="号")
                _logger.i(format_time, is_show=False)
                _logger.v(f"{i + 1:2d}. [{task_type_list[task['task_type']]}]"
                          + f"[{over_status_list[task['over_status']]}] {task['task_name']:20s}"
                          + f"（{task['score']:2.1f}分） {format_time}{time_type_list[task['over_status']]}")
            _logger.v("\n#.  以空格分割可一次性选择多个任务")
            _logger.v(f"#.  你可以在“main{CONFIG_DIR_PATH[1:]}config.txt文件”中修改配置项以控分/修改做题时间间隔等")
            _logger.v("\n\n0.  选择全部任务\n\n请输入序号：", end="")
            choose = ' '.join(input("").split()).split(" ")
            _logger.v(choose, is_show=False)
            task_choose_list = []
            tem_flag = True
            if CDRTask.check_input_data(choose[0], 0):
                task_choose_list = task_list
            else:
                for c in choose:
                    if not CDRTask.check_input_data(c, len(task_list)):
                        tem_flag = False
                        Tool.cls()
                        _logger.i("输入格式有误！\n")
                        break
                    task_choose_list.append(task_list[int(c) - 1])
            if tem_flag:
                break
        # 课程单词预处理加载
        _logger.i("预加载任务所需题库中......")
        for task in task_choose_list:
            # 未过期任务
            #   over_status为任务标识，1：未开始 2：进行中 3：已过期
            #   release_id任务对应的模板id（相当于类）
            #   task_id任务对应的实际情况（相当于类所实例化的对象），为-1时代表还未申请
            #   task_type为任务类型标识（未证实） 1：学习任务 2：测试任务
            course_id = task.get("course_id") or re.match(r'.*/(.*)\.jpg', task["course_img_url"]).group(1)
            self._tasks.add_task([
                self.do_task(task, course_id, await self.get_course_by_task(task))
                for _ in range(settings.multiple_task)
            ])
        Tool.cls()
        await self.start_task()
        _logger.i("本次全部任务已完成！")
        input("按回车键返回上一级")

    async def do_task(self, task, course_id, course):
        time_out = settings.timeout
        is_random_score = settings.is_random_score
        is_show = not settings.is_multiple_chapter
        if task['free'] != 1:
            _logger.w("该任务疑似收费，你可能未开通对应课程权限或权限已到期")
            _logger.w("若你在公众号可以正常进入此任务，可以按回车继续任务运行，期间可能会出现意料之外的情况\n")
            _logger.i("若想跳过该任务，请按Ctrl+C\n")
            try:
                input("按回车继续")
            except KeyboardInterrupt:
                return
        if task['over_status'] == 2:
            task_type = task["task_type"]
            release_id = task["release_id"]
            now_score = CDRTask.get_random_score(is_open=is_random_score)
            _logger.i("course_id:" + course_id, is_show=False)
            _logger.d(course.data)
            _logger.i("开始做【" + task["task_name"] + "】，目标分数：" + str(now_score), is_show=is_show)
            answer = Answer(course)
            _logger.i("题库装载完毕！", is_show=is_show)
            count = 0
            while True:
                count += 1
                if count > 2:
                    _logger.w("相同任务重复答题次数过多，疑似存在无法找到答案的题目，跳过该任务", is_show=is_show)
                    break
                _logger.i("模拟加载流程", is_show=is_show)
                task_id = await ClassTask.get_task_id(task)
                if task_type == 1:
                    #   模拟加载流程
                    _logger.i("班级-学习任务", is_show=is_show)
                    # 处理taskId为-1的情况
                    await asyncio.sleep(1)
                data = {
                    "task_id": task_id,
                    "task_type": task_type,
                    "release_id": release_id,
                    "timestamp": Tool.time(),
                    "versions": CDR_VERSION
                }
                res = await requests.get(url='https://gateway.vocabgo.com/Student/ClassTask/StartAnswer',
                                         headers=settings.header, params=data, timeout=time_out)
                json_data = await res.json()
                res.close()
                if json_data["code"] == 21006:
                    await self.verify_human(task_id)
                    data["timestamp"] = Tool.time()
                    res = await requests.get(url='https://gateway.vocabgo.com/Student/ClassTask/StartAnswer',
                                             headers=settings.header, params=data, timeout=time_out)
                    json_data = await res.json()
                    res.close()
                if task_type == 1:
                    #   判断是否需要选词
                    try:
                        if json_data["code"] == 20001 and await ClassTask.choose_word(task_id, task_type):
                            break
                    except NoPermission as e:
                        _logger.w(e)
                        _logger.w("疑似未开通VIP课程，请自行购买VIP课程或反馈至学校购买后再进行答题操作")
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
                    res = await requests.get(url='https://gateway.vocabgo.com/Student/ClassTask/StartAnswer',
                                             headers=settings.header, params=data, timeout=time_out)
                    json_data = await res.json()
                    res.close()
                    if json_data["code"] == 21006:
                        await self.verify_human(task_id)
                        data["timestamp"] = Tool.time()
                        res = await requests.get(url='https://gateway.vocabgo.com/Student/ClassTask/StartAnswer',
                                                 headers=settings.header, params=data, timeout=time_out)
                        json_data = await res.json()
                        res.close()
                    await asyncio.sleep(1)
                    if json_data["code"] == 0 and json_data["msg"] is not None \
                            and json_data["msg"].find("返回首页") != -1:
                        _logger.i("任务信息加载失败，返回上一级重选任务即可", is_show=is_show)
                        input("按回车返回上一级")
                        return
                    #   判断是否跳过学习阶段
                    _logger.i(json_data, is_show=False)
                    if json_data["data"]["topic_mode"] == 0:
                        json_data = await ClassTask.skip_learn_task(json_data["data"]["topic_code"])
                        _logger.i("已跳过学习阶段", is_show=is_show)
                else:
                    _logger.i("班级-测试任务", is_show=is_show)
                    # 开始任务包
                    await asyncio.sleep(1)
                _logger.i("开始答题\n", is_show=is_show)
                if json_data["code"] == 0:
                    _logger.w(json_data["msg"], is_show=is_show)
                    return
                if settings.is_multiple_chapter:
                    _logger.i(json_data, is_show=False)
                    self.add_progress(str(release_id), task['task_name'], json_data['data']['topic_total'])
                    self.update_progress(str(release_id), 0)
                # 提交做题
                #   code=20004时代表当前题目已做完，测试任务完成标志
                #   code=20001需要选词，学习任务完成标志
                while json_data["code"] != 20004 and json_data["code"] != 20001 and \
                        json_data["data"]["topic_done_num"] <= json_data["data"]["topic_total"]:
                    if settings.is_multiple_chapter:
                        self.update_progress(str(release_id), json_data["data"]["topic_done_num"])
                    json_data = await self.do_question(answer, json_data, release_id, now_score, task_id)
                    if json_data["code"] == 0 and json_data["msg"].find("返回首页重新加载") != -1:
                        _logger.w("意外的返回情况")
                        _logger.w(json_data["msg"])
                        _logger.w("本次任务稍后将重新开始")
                        break
                if is_show:
                    _logger.i(f"【{task['task_name']}】已完成。分数：{await ClassTask.get_class_task_score(release_id)}")
                else:
                    self.finish_progress(str(release_id), f"分数：{await ClassTask.get_class_task_score(release_id)}")
                if json_data["code"] == 20004:
                    break
                if now_score <= await ClassTask.get_class_task_score(release_id):
                    break
        else:
            _logger.i(f"该【{task['task_name']}】任务未开始")

    @staticmethod
    async def get_task_list():
        time_out = settings.timeout
        task_type_list = ["未知", "学习", "测试"]
        over_status_list = ["未知", "未开始", "进行中", "已过期"]
        res = await requests.get(
            url=f'https://gateway.vocabgo.com/Student/ClassTask/List?page_count=1&page_size=20&timestamp={Tool.time()}'
                + f'&versions={CDR_VERSION}', headers=settings.header, timeout=time_out
        )
        task_list = (await res.json())['data']['task_list']
        _logger.i(task_list, is_show=False)
        res.close()
        tem_list = []
        count = 2
        flag = True
        while flag:
            for i in task_list:
                #   排除已过期任务及已完成任务
                _logger.i(i, is_show=False)
                _logger.i(f"[{task_type_list[i['task_type']]}][{over_status_list[i['over_status']]}] "
                          f"{i['task_name']} （{i['score']}分）", is_show=False)
                if i['over_status'] != 3 and (i["task_type"] == 1 and i['score'] != 100 or i['progress'] != 100):
                    tem_list.append(i)
            if len(task_list) != 20:
                flag = False
            else:
                # 模拟预请求
                (await requests.options(
                    url=f'https://gateway.vocabgo.com/Student/ClassTask/List?page_count={count:d}&page_size=20'
                    f'&timestamp={Tool.time()}&versions={CDR_VERSION}', headers=settings.header, timeout=time_out
                )).close()
                response = await requests.get(
                    url=f'https://gateway.vocabgo.com/Student/ClassTask/List?page_count={count:d}&page_size=20'
                    f'&timestamp={Tool.time()}&versions={CDR_VERSION}', headers=settings.header, timeout=time_out
                )
                task_list = (await response.json())['data']['task_list']
                response.close()
                count += 1
        return tem_list

    @staticmethod
    async def get_task_id(task: dict) -> int:
        if task["task_id"] != -1:
            return task["task_id"]
        data = {
            "task_id": task["task_id"],
            "release_id": task["release_id"],
            "timestamp": Tool.time(),
            "versions": CDR_VERSION,
        }
        (await requests.options("https://gateway.vocabgo.com/Student/ClassTask/Info",
                                params=data, headers=settings.header, timeout=settings.timeout)).close()
        res = await requests.get("https://gateway.vocabgo.com/Student/ClassTask/Info",
                                 params=data, headers=settings.header, timeout=settings.timeout)
        json_data = (await res.json())
        res.close()
        if json_data["code"] == 1:
            return json_data["data"]["task_id"]
        for task_info in await ClassTask.get_task_list():
            if task_info["release_id"] == task["release_id"]:
                if task_info["task_id"] != -1:
                    return task_info["task_id"]
                break
        data["timestamp"] = Tool.time()
        data["task_type"] = task["task_type"]
        (await requests.options(url='https://gateway.vocabgo.com/Student/ClassTask/StartAnswer',
                                headers=settings.header, params=data, timeout=settings.timeout)).close()
        res = await requests.get(url='https://gateway.vocabgo.com/Student/ClassTask/StartAnswer',
                                 headers=settings.header, params=data, timeout=settings.timeout)
        json_data = await res.json()
        res.close()
        if json_data["code"] == 1:
            return json_data["data"]["task_id"]
        return task["task_id"]

    @staticmethod
    async def choose_word(task_id: int, task_type: int) -> bool:
        is_show = not settings.is_multiple_chapter
        time_out = settings.timeout
        _logger.i("需要选词", is_show=is_show)
        res = await requests.get(
            url=f'https://gateway.vocabgo.com/Student/ClassTask/ChoseWordList?task_id={task_id}'
            f'&task_type={task_type}&timestamp={Tool.time()}&versions={CDR_VERSION}',
            headers=settings.header, timeout=time_out)
        json_data = await res.json()
        res.close()
        if json_data["code"] == 0 and json_data["msg"].find("开通权限") != -1:
            raise NoPermission(json_data["msg"])
        word_map = {}
        for word in json_data['data']['word_list']:
            if word['score'] != 10:
                # 为何要多次一举不直接使用参数course_id呢
                # 那是因为自建词表任务中course_id恒为course_self，与实际情况不一致
                tem_str = word["course_id"] + ':' + word["list_id"]
                if word_map.get(tem_str) is None:
                    word_map[tem_str] = []
                word_map[tem_str].append(word['word'])
        if len(word_map) == 0:
            _logger.i("当前学习任务已完成", is_show=is_show)
            return True
        _logger.i(word_map, is_show=False)
        index = 0
        word_map_len = 0
        for k in word_map:
            word_map_len += len(word_map[k])
        while word_map_len < 5:
            word = json_data['data']['word_list'][index]
            tem_str = word["course_id"] + ':' + word["list_id"]
            if word['word'] not in word_map[tem_str]:
                if word_map.get(tem_str) is None:
                    word_map[tem_str] = []
                word_map[tem_str].append(word['word'])
                _logger.i(f"单词复选：{word['word']}", is_show=False)
            index = index + 1

            word_map_len = 0
            for k in word_map:
                word_map_len += len(word_map[k])
        _logger.i(word_map, is_show=False)
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
        res = await requests.post(
            url='https://gateway.vocabgo.com/Student/ClassTask/SubmitChoseWord',
            headers=settings.header, json=data, timeout=time_out)
        _logger.i(await res.json(), is_show=False)
        res.close()
        _logger.i("选词完毕！", is_show=is_show)
        return False

    @staticmethod
    async def skip_learn_task(topic_code: str):
        is_show = not settings.is_multiple_chapter
        #   模拟加载流程
        _logger.i("正在跳过学习任务的学习阶段", is_show=is_show)
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
        res = await requests.post(
            url='https://gateway.vocabgo.com/Student/ClassTask/SubmitAnswerAndSave',
            json=data, headers=settings.header, timeout=settings.timeout)
        json_data = await res.json()
        res.close()
        await asyncio.sleep(1)
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
        res = await requests.post(
            url='https://gateway.vocabgo.com/Student/ClassTask/SkipNowTopicMode',
            json=data, headers=settings.header, timeout=settings.timeout)
        json_data = await res.json()
        res.close()
        return json_data

    @staticmethod
    async def get_class_task_score(release_id):
        (await requests.options(
            url='https://gateway.vocabgo.com/Student/ClassTask/List?page_count=1&page_size=10&timestamp='
                + f'{Tool.time()}&versions={CDR_VERSION}', headers=settings.header, timeout=settings.timeout)).close()
        res = await requests.get(
            url='https://gateway.vocabgo.com/Student/ClassTask/List?page_count=1&page_size=100&timestamp='
                + f'{Tool.time()}&versions={CDR_VERSION}', headers=settings.header, timeout=settings.timeout)
        json_data = await res.json()
        res.close()
        for task in json_data['data']['task_list']:
            if task["release_id"] == release_id:
                return task["score"]
        return 0

    async def do_question(self, answer: Answer, json_data: dict, release_id, now_score, task_id: int) -> dict:
        is_show = not settings.is_multiple_chapter
        _logger.i(str(json_data["data"]["topic_done_num"])
                  + "/" + str(json_data["data"]["topic_total"]) + ".", end='', is_show=is_show)
        if now_score != 100 and 100.0 * json_data["data"]["topic_done_num"] / \
                json_data["data"]["topic_total"] + 5 >= now_score:
            if not settings.is_random_time:
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(2)
            if await ClassTask.get_class_task_score(release_id) >= now_score:
                _logger.i(f"[mode:{json_data['data']['topic_mode']}]{json_data['data']['stem']['content']}"
                          + "   已达本次既定分数，超时本题！", is_show=is_show)
                json_data = await CDRTask.skip_answer(json_data["data"]["topic_code"],
                                                      json_data["data"]["topic_mode"],
                                                      "ClassTask")
            else:
                json_data = await self.find_answer_and_finish(answer, json_data["data"], task_id)
        else:
            json_data = await self.find_answer_and_finish(answer, json_data["data"], task_id)
        #   每10道题清理一次gc
        if json_data.get("data") is None:
            _logger.e(json_data, is_show=False)
        if json_data["code"] == 1 and json_data["data"]["topic_done_num"] % 10 == 0:
            gc.collect()
            gc.set_debug(gc.DEBUG_UNCOLLECTABLE)
        return json_data
