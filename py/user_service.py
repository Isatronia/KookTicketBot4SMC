# -*- encoding: utf-8 -*-
'''
@File    :   user_service.py
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/11 15:55   ishgrina   1.0         None
'''

# import libs
import json
import logging
import asyncio
from typing import Union
from asyncio import Lock


class UserServiceImpl:
    data: dict = {}
    lock: Lock = Lock()

    def __init__(self):
        try:
            with open('../cfg/user.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

    async def get(self, key) -> Union[dict, None]:
        async with self.lock:
            try:
                return self.data[key]
            except KeyError:
                return None

    async def set(self, key, value) -> None:
        async with self.lock:
            self.data[key] = value
            with open('../cfg/user.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

    async def get_guild_cnt(self, user_id, guild_id) -> Union[int, None]:
        async with self.lock:
            try:
                user = self.data[user_id]
                try:
                    return self.data[user_id][guild_id]
                except KeyError:
                    self.data[user_id][guild_id] = 0
                    return 0
            except KeyError:
                self.data[user_id] = {guild_id: 0}
                return 0

    async def set_guild_cnt(self, user_id, guild_id, cnt) -> None:
        async with self.lock:
            try:
                user = self.data[user_id]
                try:
                    self.data[user_id][guild_id] = cnt
                except KeyError:
                    self.data[user_id][guild_id] =  cnt
            except KeyError:
                self.data[user_id] = {guild_id: cnt}
            with open('../cfg/user.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

    async def open(self, user_id, guild_id):
        async with self.lock:
            try:
                if user_id not in self.data:
                    self.data[user_id] = {guild_id: 1}
                else:
                    self.data[user_id][guild_id] += 1
            except KeyError:
                self.data[user_id] = {guild_id: 1}
            with open('../cfg/user.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

    async def close(self, user_id, guild_id):
        async with self.lock:
            try:
                if user_id not in self.data:
                    self.data[user_id] = {guild_id: 0}
                try:
                    if self.data[user_id][guild_id] > 0:
                        self.data[user_id][guild_id] -= 1
                except KeyError:
                    self.data[user_id] = {guild_id: 0}
            except KeyError:
                self.data[user_id] = {guild_id: 0}
            with open('../cfg/user.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

    # 重置某个用户在特定guild的所有数据
    async def reset(self, user_id, guild_id):
        async with self.lock:
            if user_id in self.data:
                self.data[user_id][guild_id] = 0
            else:
                self.data[user_id] = {guild_id: 0}
            with open('../cfg/user.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)




class UserService:
    __instance: UserServiceImpl = None
    __lock: Lock = Lock()

    @staticmethod
    async def get_instance() -> UserServiceImpl:
        if UserService.__instance is None:
            async with UserService.__lock:
                if UserService.__instance is None:
                    UserService.__instance = UserServiceImpl()
        return UserService.__instance

    def __new__(cls, *args, **kwargs):
        with UserService.__lock:
            if not isinstance(cls.__instance, cls):
                cls.__instance = cls.__instance or cls(*args, **kwargs)
        return cls.__instance
