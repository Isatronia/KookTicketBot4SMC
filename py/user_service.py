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
from typing import Union
from asyncio import Lock
from khl import Message
from .value import PATH

'''
文件数据结构 - 已重构
user.json:
{
    ${guild_id}:{
        ${user_id}: {'cnt': 0, 'keys': dict}
    }
}
'''
log = logging.getLogger(__name__)

class UserServiceImpl:
    _data: dict = {}
    _wlock: Lock = Lock()
    _rlock: Lock = Lock()
    _flock: Lock = Lock()

    def __init__(self):
        self._load()
    
    def _get_data(self):
        return UserServiceImpl._data
    
    def _load(self):
        try:
            with open(PATH.USER_DATA, 'r', encoding='utf-8') as f:
                UserServiceImpl._data = json.load(f)
        except FileNotFoundError:
            log.warning(
                "User data file does not exists." +
                " Please Check working directory if it's not the first time running this bot.")
            UserServiceImpl._data = {}
    
    def _store(self):
        try:
            with open(PATH.USER_DATA, 'w', encoding='utf-8') as f:
                json.dump(self._get_data(), f, ensure_ascii=False, indent=4)
        except FileNotFoundError:
            log.error(f"Could not create file {PATH.USER_DATA}, please check env.")
        except BaseException as e:
            log.error(e)
    
    async def get(self, key) -> Union[dict, None]:
        async with UserServiceImpl._rlock:
            try:
                return self._get_data()[key]
            except KeyError:
                return None
    
    async def set(self, key, value) -> None:
        async with UserServiceImpl._wlock and UserServiceImpl._rlock:
            self._get_data()[key] = value
            await self.store()

    async def store(self):
        async with UserServiceImpl._flock:
            self._store()

    async def try_set_user_key(self, user_id, guild_id, key, value):
        # 这段挺蠢的，等等重构。
        async with UserServiceImpl._wlock and UserServiceImpl._rlock:
            if guild_id not in self._get_data():
                self._get_data()[guild_id] = {user_id: {"cnt": 0, 'keys': {key: value}}}
            elif user_id not in self._get_data()[guild_id]:
                self._get_data()[guild_id][user_id] = {"cnt": 0, "keys": {key: value}}
            elif "keys" not in self._get_data()[guild_id][user_id]:
                self._get_data()[guild_id][user_id]["keys"] = {key: value}
            else:
                self._get_data()[guild_id][user_id]["keys"][key] = value
            await self.store()

    # 尝试返回指定的值
    async def try_get_user_key(self, user_id=None, guild_id=None, key=None, message: Union[Message, None] = None):
        async with UserServiceImpl._rlock:
            if message is not None:
                user_id = message.author.id
                guild_id = message.ctx.guild.id
            try:
                return self._get_data()[guild_id][user_id]["keys"][key]
            except KeyError:
                return None

    async def get_guild_cnt(self, user_id, guild_id) -> Union[int, None]:
        async with UserServiceImpl._rlock:
            if guild_id not in self._get_data():
                self._get_data()[guild_id] = {user_id: {'cnt': 0}}
                return 0
            if user_id not in self._get_data()[guild_id]:
                self._get_data()[guild_id][user_id] = {'cnt': 0}
                return 0
            return self._get_data()[guild_id][user_id]['cnt']

    async def set_guild_cnt(self, user_id, guild_id, cnt) -> None:
        async with UserServiceImpl._wlock and UserServiceImpl._rlock:
            if guild_id not in self._get_data():
                self._get_data()[guild_id] = {user_id: {'cnt': cnt}}
            elif user_id not in self._get_data()[guild_id]:
                self._get_data()[guild_id][user_id] = {'cnt': cnt}
            else:
                self._get_data()[guild_id][user_id] = {'cnt': cnt}
            await self.store()

    # 开票
    async def open(self, user_id, guild_id):
        try:
            int(user_id)
        except TypeError:
            log.error("User Id must be number.")
            return
        async with UserServiceImpl._wlock and UserServiceImpl._rlock:
            try:
                if guild_id not in self._get_data():
                    self._get_data()[guild_id] = {user_id: {'cnt': 1}}
                elif user_id not in self._get_data()[guild_id]:
                    self._get_data()[guild_id][user_id] = {'cnt': 1}
                else:
                    self._get_data()[guild_id][user_id]['cnt'] += 1
            except KeyError:
                self._get_data()[guild_id] = {user_id: {'cnt': 1}}
            await self.store()

    async def close(self, user_id, guild_id):
        async with UserServiceImpl._wlock and UserServiceImpl._rlock:
            try:
                if guild_id not in self._get_data():
                    self._get_data()[guild_id] = {user_id: {'cnt': 0}}
                elif user_id not in self._get_data()[guild_id]:
                    self._get_data()[guild_id][user_id] = {'cnt': 0}
                else:
                    if self._get_data()[guild_id][user_id]['cnt'] > 0:
                        self._get_data()[guild_id][user_id]['cnt'] -= 1
                    else:
                        self._get_data()[guild_id][user_id]['cnt'] = 0
            except KeyError:
                self._get_data()[guild_id] = {user_id: {'cnt': 0}}
            await self.store()

    # 重置某个用户在特定guild的所有数据
    async def reset(self, user_id, guild_id):
        async with UserServiceImpl._wlock and UserServiceImpl._rlock:
            if guild_id not in self._get_data():
                self._get_data()[guild_id] = {user_id: {'cnt': 0}}
            elif user_id not in self._get_data()[guild_id]:
                self._get_data()[guild_id][user_id] = {'cnt': 0}
            else:
                self._get_data()[guild_id][user_id]['cnt'] = 0
            await self.store()


user_service = UserServiceImpl()

# class UserService:
#     __instance: UserServiceImpl = None
#     __lock: Lock = Lock()
#
#     @staticmethod
#     async def get_instance() -> UserServiceImpl:
#         if UserService.__instance is None:
#             async with UserService.__lock:
#                 if UserService.__instance is None:
#                     UserService.__instance = UserServiceImpl()
#         return UserService.__instance
#
#     def __new__(cls, *args, **kwargs):
#         with UserService.__lock:
#             if not isinstance(cls.__instance, cls):
#                 cls.__instance = cls.__instance or cls(*args, **kwargs)
#         return cls.__instance
