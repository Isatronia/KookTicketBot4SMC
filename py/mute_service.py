# -*- encoding: utf-8 -*-
'''
@File    :   mute_service.py    
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/15 8:09   ishgrina   1.0         None
'''
'''
本文件中的程序用于处理禁言相关服务。
禁言数据格式为：
{
    "user_id": {
        "guild_id": {
            "mute_time": when muted, timestamp
            "contains" : time contains, in milliseconds
        }
    }
}
数据项说明：
    user_id(str)：用户ID
    guild_id(str)：服务器ID
    mute_time(int)：禁言时间，单位为秒
'''

# import lib
import asyncio
import time
import json
from asyncio import Lock
from typing import Union
from datetime import datetime, timedelta


class MuteServiceImpl:
    data: dict = None
    io_lock: Lock = Lock()
    mtd_lock: Lock = Lock()
    chk_lock: Lock = Lock()

    def __init__(self):
        async with self.io_lock:
            if self.data is None:
                try:
                    if self.data is None:
                        with open('../cfg/mute.json', 'r', encoding='utf-8') as f:
                            self.data = json.load(f)
                except FileNotFoundError:
                    self.data = {}

    async def get_guild_cnt(self, user_id, guild_id) -> Union[dict, None]:
        async with self.mtd_lock:
            if user_id not in self.data:
                self.data[user_id] = {}
            if guild_id not in self.data[user_id]:
                self.data[user_id][guild_id] = {}
            return self.data[user_id][guild_id]

    async def set_guild_cnt(self, user_id: str, guild_id: str, mute_time: int) -> None:
        async with self.mtd_lock:
            if user_id not in self.data:
                self.data[user_id] = {}
            if guild_id not in self.data[user_id]:
                self.data[user_id][guild_id] = {}
            self.data[user_id][guild_id]["mute_time"] = time.time()
            self.data[user_id][guild_id]["contains"] = mute_time

    async def is_timeup(self, user_id: str, guild_id: str) -> bool:
        async with self.mtd_lock:
            if user_id not in self.data:
                return False
            if guild_id not in self.data[user_id]:
                return False
            if "mute_time" not in self.data[user_id][guild_id]:
                del self.data[user_id][guild_id]
                return False
            if "contains" not in self.data[user_id][guild_id]:
                del self.data[user_id][guild_id]
                return False
            if time.time() - self.data[user_id][guild_id]["mute_time"] > self.data[user_id][guild_id]["contains"]:
                # clean this Record
                del self.data[user_id][guild_id]
                async with self.io_lock:
                    with open('../cfg/mute.json', 'w', encoding='utf-8') as f:
                        json.dump(self.data, f, ensure_ascii=False, indent=4)
                return True
            return False

    async def check(self) -> list:
        async with self.chk_lock:
            res = []
            for user_id in self.data:
                for guild_id in self.data[user_id]:
                    if await self.is_timeup(user_id, guild_id):
                        res.append((user_id, guild_id))
            return res


class MuteService:
    lock: Lock = Lock()
    instance: MuteServiceImpl = None

    @staticmethod
    async def get_instance():
        if MuteService.instance is None:
            async with MuteService.lock:
                if MuteService.instance is None:
                    MuteService.instance = MuteServiceImpl()
        return MuteService.instance
