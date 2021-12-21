#!/usr/bin/env python
# -*- coding:utf-8 -*-
# cython : language_level=3
# @Time  : 2020-12-30, 0030 16:09
# @Author: 佚名
# @File  : tasks.py
import asyncio


class Tasks:

    def __init__(self, max_async, loop=None):
        #self.loop = loop or asyncio.get_event_loop()
        self.loop = asyncio.get_event_loop()
        #self._queue = asyncio.Queue(maxsize=100, loop=self.loop)
        self._queue = asyncio.Queue(maxsize=100) #3.10之后的Python不需要loop参数
        self.max_async = max_async
        self.work_list = []

    async def run(self):
        # ensure_future将协程转换成任务，并投递到事件循环
        works = [asyncio.ensure_future(self.__work(), loop=self.loop) for _ in range(self.max_async)]
        self.work_list.extend(works)
        await self._queue.join()
        for w in works:
            w.cancel()
        # Wait until all worker tasks are cancelled.
        await asyncio.gather(*works)

    async def __work(self):
        try:
            while True:
                fs = await self._queue.get()
                await asyncio.gather(*fs)
                self._queue.task_done()
        except asyncio.CancelledError as e:
            pass
        except Exception as e:
            # 当发生异常时，清除队列所有剩余任务
            self._queue.task_done()
            while not self._queue.empty():
                fs = self._queue.get_nowait()
                for future in fs:
                    future.close()
                self._queue.task_done()
            raise e

    def add_task(self, fs):
        if asyncio.futures.isfuture(fs) or asyncio.coroutines.iscoroutine(fs):
            raise TypeError(f"expect a list of futures, not {type(fs).__name__}")
        if not fs:
            raise ValueError('Set of coroutines/Futures is empty.')
        self._queue.put_nowait(fs)

    @property
    def count(self):
        return self._queue.qsize()

    def print_status(self):
        for w in self.work_list:
            print(w.done())
