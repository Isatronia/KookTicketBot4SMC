# -*- encoding: utf-8 -*-
'''
@File    :   mute_service.py    
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/15 8:09   ishgrina   1.0         None
'''
import logging
import queue

'''
本文件中的程序用于处理禁言相关服务。
禁言数据格式为：
{
    "user_id": {
        "guild_id": 
            "mute_time": when unmuted, timestamp
    }
}
禁言队列消息格式为：
(time, guild, user)
数据项说明：
    user_id(str)：用户ID
    guild_id(str)：服务器ID
    mute_time(int)：禁言时间，单位为秒
'''

# import lib
import time
import json
from asyncio import Lock
from typing import Union

from .utils import PriorityQueue
from .value import PATH


class MuteServiceImpl:
    _data: dict = None
    _mute_que = PriorityQueue()
    # rlock: Lock = Lock()
    wlock: Lock = Lock()
    qlock: Lock = Lock()
    # chk_lock: Lock = Lock()

    def __init__(self):
        if self._data is None:
            try:
                if self._data is None:
                    with open(PATH.MUTE_DATA, 'r', encoding='utf-8') as f:
                        self._data = json.load(f)
            except FileNotFoundError:
                self._data = {}

    async def get_guild_cnt(self, user_id, guild_id) -> Union[float, None]:
        if user_id not in self._data:
            self._data[user_id] = {}
        if guild_id not in self._data[user_id]:
            return 0.
        return self._data[user_id][guild_id]

    async def set_guild_cnt(self, user_id: str, guild_id: str, mute_time: float) -> None:
        async with self.wlock and self.qlock:
            if user_id not in self._data:
                self._data[user_id] = {}
            self._data[user_id][guild_id] = mute_time
            self._mute_que.put((mute_time, guild_id, user_id))
            with open(PATH.MUTE_DATA, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=4)

    async def is_timeup(self, user_id: str, guild_id: str) -> bool:
        if user_id not in self._data:
            return False
        if guild_id not in self._data[user_id]:
            return False
        # 到时间了，解除禁言
        if time.time() >= self._data[user_id][guild_id]:
            logging.info('user mute times up:' + user_id)
            # clean this Record
            # await self.unmute(user_id, guild_id)
            return True
        return False

    async def check(self) -> list:
        async with self.wlock:
            res = []
            for user_id in self._data:
                for guild_id in self._data[user_id]:
                    if await self.is_timeup(user_id, guild_id):
                        res.append({'user_id': user_id, 'guild_id': guild_id})
        return res

    async def mute(self, guild: str, user: str, mute_time: float) -> None:
        await self.set_guild_cnt(user, guild, mute_time)

    async def unmute(self, user: str, guild: str) -> None:
        async with self.wlock:
            logging.info('user unmuted:' + user)
            if user not in self._data:
                return
            if guild not in self._data[user]:
                return
            # clean this Record
            del self._data[user][guild]
            if len(self._data[user]) == 0:
                del self._data[user]
            with open(PATH.MUTE_DATA, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=4)

    async def queue_refresh(self):
        if self._data is None:
            return
        async with self.wlock and self.qlock:
            self._mute_que = PriorityQueue()
            for u in self._data:
                for g in u:
                    for t in g:
                        self._mute_que.put((t, g, u))
        return

    async def query_nearest_unmute_user(self):
        async with self.qlock:
            return self._mute_que.peek()



mute_service = MuteServiceImpl()


# class MuteService:
#     lock: Lock = Lock()
#     instance: MuteServiceImpl = None
#
#     @staticmethod
#     async def get_instance():
#         if MuteService.instance is None:
#             async with MuteService.lock:
#                 if MuteService.instance is None:
#                     MuteService.instance = MuteServiceImpl()
#         return MuteService.instance
