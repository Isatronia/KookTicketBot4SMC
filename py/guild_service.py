# -*- encoding: utf-8 -*-
'''
@File    :   guild_service.py
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/11 7:55   ishgrina   1.0         None
'''

# import lib
import json
from asyncio import Lock
from typing import Union
from .user_service import UserService, UserServiceImpl


class GuildServiceImpl:
    data: dict = {}
    io_lock: Lock = Lock()
    init_lock: Lock = Lock()

    def __init__(self):
        try:
            with open('../cfg/data.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

    # 初始化服务器信息
    async def init_guild(self, guild_id):
        if guild_id not in self.data:
            async with self.init_lock:
                if guild_id not in self.data:
                    self.data[guild_id] = {'cnt': 1, 'role': {}, 'channel': {}}

    # 获取服务器信息
    async def get(self, guild_id) -> dict:
        async with self.io_lock:
            return self.data[guild_id]

    # 获取服务器角色信息
    async def get_role(self, guild_id, role_name) -> Union[str, None]:
        async with self.io_lock:
            try:
                return self.data[guild_id]['role'][role_name]
            except KeyError:
                return None

    # 设置服务器角色信息
    async def set_role(self, guild_id, role_tag, role_id):
        async with self.io_lock:
            if guild_id not in self.data:
                await self.init_guild(guild_id)
            self.data[guild_id]['role'][role_tag] = role_id
            with open('../cfg/data.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

    # 获取服务器频道信息
    async def get_channel(self, guild_id, channel_tag) -> Union[str, None]:
        async with self.io_lock:
            try:
                return self.data[guild_id]['channel'][channel_tag]
            except KeyError:
                return None

    # 设置服务器频道信息
    async def set_channel(self, guild_id, channel_tag, channel_id):
        async with self.io_lock:
            if guild_id not in self.data:
                await self.init_guild(guild_id)
            if 'channel' not in self.data[guild_id]:
                self.data[guild_id]['channel'] = {}
            self.data[guild_id]['channel'][channel_tag] = channel_id
            with open('../cfg/data.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

    # 申请服务器Ticket
    async def apply(self, guild_id, user_id) -> Union[int, None]:
        async with self.io_lock:
            userService = await UserService.get_instance()
            userGuildCnt = await userService.get_guild_cnt(user_id, guild_id)
            if 2 <= userGuildCnt:
                return None
            await userService.open(user_id, guild_id)
            self.data[guild_id]['cnt'] += 1
            with open('../cfg/data.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            return self.data[guild_id]['cnt']

    # 释放服务器Ticket
    async def close(self, guild_id, user_id):
        async with self.io_lock:
            userService = await UserService.get_instance()
            await userService.close(user_id, guild_id)

    # 检查指定服务器是否有效
    async def record_if_not_exist(self, guild_id):
        async with self.io_lock:
            if guild_id not in self.data:
                await self.init_guild(guild_id)
            return

    async def get_staff(self, guild_id) -> Union[int, None]:
        return await self.get_role(guild_id, 'staff')

    async def get_mute(self, guild_id) -> Union[str, None]:
        return await self.get_role(guild_id, 'mute')

    async def set_staff(self, guild_id, role_id):
        await self.set_role(guild_id, 'role', role_id)


# 单例模式， 保证只有一个id_dict实例
class GuildService:
    __instance: GuildServiceImpl = None
    __lock = Lock()

    @staticmethod
    async def get_instance():
        if GuildService.__instance is None:
            async with GuildService.__lock:
                if GuildService.__instance is None:
                    GuildService.__instance = GuildServiceImpl()
        return GuildService.__instance

    def __new__(cls):
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = GuildServiceImpl()
        return cls.__instance

    def __getitem__(self, key):
        return self.__instance[key]

    def __setitem__(self, key, value):
        self.__instance[key] = value
