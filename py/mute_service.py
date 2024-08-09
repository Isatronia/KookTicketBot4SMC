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
            {mute_time:float} when unmuted, timestamp
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

log = logging.getLogger(__name__)

class MuteServiceImpl:
    _data: dict = None
    _mute_que = PriorityQueue()
    # 文件锁，文件读写用
    _flock: Lock = Lock()
    # 写锁，内存数据读写用
    _wlock: Lock = Lock()
    # 队列锁，禁言时间通知队列用
    _qlock: Lock = Lock()

    def __init__(self):
        self._load()

    def _load(self):
        if self._get_data() is None:
            try:
                if self._get_data() is None:
                    with open(PATH.MUTE_DATA, 'r', encoding='utf-8') as f:
                        MuteServiceImpl._data = json.load(f)
            except FileNotFoundError:
                log.error(f"Mute Data file not found. Initializing...")
                MuteServiceImpl._data = {}

    def _store(self):
        with open(PATH.MUTE_DATA, 'w', encoding='utf-8') as f:
            json.dump(self._get_data(), f, ensure_ascii=False, indent=4)

    def _get_data(self):
        return MuteServiceImpl._data
    
    def _get_queue(self):
        return MuteServiceImpl._mute_que

    async def load(self):
        async with MuteServiceImpl._flock:
            self._load()

    async def store(self):
        async with MuteServiceImpl._flock:
            self._store()

    async def get_guild_cnt(self, user_id, guild_id) -> Union[float, None]:
        if user_id not in self._get_data():
            self._get_data()[user_id] = {}
        if guild_id not in self._get_data()[user_id]:
            return 0.
        return self._get_data()[user_id][guild_id]

    async def set_guild_cnt(self, user_id: str, guild_id: str, mute_time: float) -> None:
        async with MuteServiceImpl._wlock and MuteServiceImpl._qlock:
            if user_id not in self._get_data():
                self._get_data()[user_id] = {}
            self._get_data()[user_id][guild_id] = mute_time
            MuteServiceImpl._mute_que.put((mute_time, guild_id, user_id))

    async def is_timeup(self, user_id: str, guild_id: str) -> bool:
        if user_id not in self._get_data():
            return False
        if guild_id not in self._get_data()[user_id]:
            return False
        # 到时间了，解除禁言
        if time.time() >= self._get_data()[user_id][guild_id]:
            log.info('user mute times up:' + user_id)
            # clean this Record
            return True
        return False

    async def check(self) -> list:
        async with MuteServiceImpl._wlock:
            res = []
            for user_id in self._get_data():
                for guild_id in self._get_data()[user_id]:
                    if await self.is_timeup(user_id, guild_id):
                        res.append({'user_id': user_id, 'guild_id': guild_id})
        return res

    async def mute(self, guild: str, user: str, mute_time: float) -> None:
        await self.set_guild_cnt(user, guild, mute_time)

    async def unmute(self, user: str, guild: str) -> None:
        async with MuteServiceImpl._wlock:
            if user not in self._get_data():
                return
            if guild not in self._get_data()[user]:
                return
            # clean this Record
            time_up = self._get_data()[user][guild]
            self._mute_que.delete((time_up, guild, user))
            del self._get_data()[user][guild]
            if len(self._get_data()[user]) == 0:
                del self._get_data()[user]
            await self.store()
            log.info('user unmuted:' + user)

    async def queue_refresh(self):
        if self._get_data() is None:
            return
        async with MuteServiceImpl._wlock and MuteServiceImpl._qlock:
            MuteServiceImpl._mute_que = PriorityQueue()
            for u in self._get_data():
                for g in u:
                    for t in g:
                        MuteServiceImpl._mute_que.put((t, g, u))
        return


    def query_nearest_unmute_user(self):
        return MuteServiceImpl._mute_que.peek()


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
