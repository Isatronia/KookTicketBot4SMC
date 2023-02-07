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
import logging
from .user_service import user_service
from .value import PATH

'''
data.json - GUILD DATA
- cnt 服务器全部 Ticket 数量
- max 服务器单人最多 Ticket 数量
- role 服务器角色（自定义）
    - id
    - permission
- channel 频道（暂时没用）
'''


class GuildServiceImpl:
    data: dict = {}
    action_lock: Lock = Lock()
    io_lock: Lock = Lock()
    init_lock: Lock = Lock()

    def __init__(self):
        try:
            with open(PATH.GUILD_DATA, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                pass
        except FileNotFoundError:
            self.data = {}

    # Save data to file
    async def save_data(self) -> None:
        async with self.io_lock:
            try:
                with open(PATH.GUILD_DATA, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logging.error(str(e))
        return None

    # Read data from file
    async def read_data(self) -> None:
        async with self.io_lock:
            try:
                with open(PATH.GUILD_DATA, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                    pass
            except FileNotFoundError:
                self.data = {}

    # 初始化服务器信息
    async def init_guild(self, guild_id):
        await  self.read_data()
        if guild_id not in self.data:
            async with self.init_lock:
                if guild_id not in self.data:
                    self.data[guild_id] = {'cnt': 1, 'role': {}, 'channel': {}}
                    await self.save_data()

    # check if guild exit in data
    async def check_guild(self, guild_id) -> None:
        async with self.action_lock:
            if guild_id not in self.data:
                await self.init_guild(guild_id)
        return

    # 获取服务器信息
    async def get(self, guild_id) -> dict:
        return self.data[guild_id]

    # 获取服务器角色信息
    async def get_role(self, guild_id, role_name) -> Union[str, None]:
        await self.read_data()
        async with self.action_lock:
            try:
                return self.data[guild_id]['role'][role_name]
            except KeyError:
                return None

    # get a dict of all roles in a guild
    async def get_roles(self, guild_id) -> Union[dict, None]:
        await self.read_data()
        async with self.action_lock:
            try:
                return self.data[guild_id]['role']
            except KeyError:
                return None

    # 设置服务器角色信息
    async def set_role(self, guild_id, role_tag, role_id):
        await self.check_guild(guild_id)
        async with self.action_lock:
            if 'role' not in self.data[guild_id]:
                self.data[guild_id]['role'] = {}

            # fit old version
            if 'id' not in self.data[guild_id]['role'][role_tag] and self.data[guild_id]['role'][role_tag]:
                self.data[guild_id]['role'][role_tag] = {'id': self.data[guild_id]['role'][role_tag], 'permission': []}

            # init role info
            self.data[guild_id]['role'][role_tag]['id'] = role_id
            self.data[guild_id]['role'][role_tag]['permission'] = []
            await self.save_data()

    # 获取服务器频道信息
    async def get_channel(self, guild_id, channel_tag) -> Union[str, None]:
        async with self.action_lock:
            await self.read_data()
            try:
                return self.data[guild_id]['channel'][channel_tag]
            except KeyError:
                return None

    # 设置服务器频道信息
    async def set_channel(self, guild_id, channel_tag, channel_id):
        await self.check_guild(guild_id)
        async with self.action_lock:
            if 'channel' not in self.data[guild_id]:
                self.data[guild_id]['channel'] = {}
            self.data[guild_id]['channel'][channel_tag] = channel_id
            await self.save_data()

    async def set_max_ticket(self, guild_id, maxium_ticket: int) -> bool:
        await self.check_guild(guild_id)
        async with self.action_lock:
            self.data[guild_id]['max'] = maxium_ticket
            return True

    # 申请服务器Ticket
    async def apply(self, guild_id, user_id) -> Union[int, None]:
        async with self.action_lock:
            userGuildCnt = await user_service.get_guild_cnt(user_id, guild_id)

            # check if max have been set, if not, set to DEFAULT value.
            if 'max' not in self.data[guild_id]:
                self.data[guild_id]['max'] = 2

            # check if over maxium limit
            if self.data[guild_id]['max'] <= userGuildCnt:
                return None

            await user_service.open(user_id, guild_id)
            self.data[guild_id]['cnt'] += 1
            with open(PATH.GUILD_DATA, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            return self.data[guild_id]['cnt']

    # 释放服务器Ticket
    async def close(self, guild_id, user_id):
        async with self.action_lock:
            await user_service.close(user_id, guild_id)

    # # 检查指定服务器是否有效
    # async def record_if_not_exist(self, guild_id):
    #     async with self.action_lock:
    #         if guild_id not in self.data:
    #             await self.init_guild(guild_id)
    #         return

    # async def get_staff(self, guild_id) -> Union[int, None]:
    #     return await self.get_role(guild_id, 'staff')
    #
    # async def get_mute(self, guild_id) -> Union[str, None]:
    #     return await self.get_role(guild_id, 'mute')
    #
    # async def set_staff(self, guild_id, role_id):
    #     await self.set_role(guild_id, 'role', role_id)


# py是天生的单例模式
guild_service = GuildServiceImpl()

# # 单例模式， 保证只有一个id_dict实例
# class GuildService:
#     __instance: GuildServiceImpl = None
#     __lock = Lock()
#
#     @staticmethod
#     async def get_instance():
#         if GuildService.__instance is None:
#             async with GuildService.__lock:
#                 if GuildService.__instance is None:
#                     GuildService.__instance = GuildServiceImpl()
#         logging.info('Getted Instance: ' + str(GuildService.__instance))
#         return GuildService.__instance
#
#     def __new__(cls):
#         if cls.__instance is None:
#             with cls.__lock:
#                 if cls.__instance is None:
#                     cls.__instance = GuildServiceImpl()
#         return cls.__instance
#
#     def __getitem__(self, key):
#         return self.__instance[key]
#
#     def __setitem__(self, key, value):
#         self.__instance[key] = value
