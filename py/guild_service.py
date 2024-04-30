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
  role_id
    - name
    - permission
- channel 频道（暂时没用）
'''

LOG_HEADER = ' [guild_service.py] '


class GuildServiceImpl:
    data: dict = {}
    action_lock: Lock = Lock()
    io_lock: Lock = Lock()
    init_lock: Lock = Lock()

    # 初始化GuildService
    def __init__(self):
        try:
            with open(PATH.GUILD_DATA, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                pass
        except FileNotFoundError:
            self.data = {}

    # 把数据保存到本地文件
    async def save_data(self) -> None:
        async with self.io_lock:
            try:
                with open(PATH.GUILD_DATA, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logging.error(str(e))
        return None

    # 从本地文件读取数据
    async def read_data(self) -> None:
        async with self.io_lock:
            try:
                with open(PATH.GUILD_DATA, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                    pass
            except FileNotFoundError:
                self.data = {}

    # 初始化服务器信息
    # 新增服务器时初始化数据
    async def init_guild(self, guild_id):
        await self.read_data()
        if guild_id not in self.data:
            async with self.init_lock:
                if guild_id not in self.data:
                    self.data[guild_id] = {'cnt': 1, 'role': {}, 'channel': {}}
                    await self.save_data()

    # 检查服务器是否在机器人的数据库中注册,如果没有就注册。
    # 用于确保访问时能够获取服务器
    async def check_guild(self, guild_id) -> None:
        async with self.action_lock:
            if guild_id not in self.data:
                await self.init_guild(guild_id)
        return

    # 获取服务器信息
    async def get(self, guild_id) -> dict:
        return self.data[guild_id]

    # 根据角色名获取 已注册在机器人数据库中的 服务器的角色信息
    async def get_role_by_name(self, guild_id, role_name) -> Union[list, None]:
        await self.read_data()
        async with self.action_lock:
            matching_ids = []
            try:
                d = self.data[guild_id]['role']
                for role_id in d:
                    if 'tag' in d[role_id] and role_name in d[role_id]['tag']:
                        matching_ids.append(role_id)
                # return self.data[guild_id]['role'][role_name]
            except KeyError:
                return None
            if len(matching_ids) == 0:
                logging.warning(f"Finding role {role_name} in {guild_id} but not found. Return None.")
                return None
                # raise KeyError("Role Not Found")
            return matching_ids

    async def get_tag_by_role_id(self, guild_id, role_id: int) -> Union[None, list]:
        await self.read_data()
        async with self.action_lock:
            try:
                if role_id in self.data[guild_id]['role']:
                    return self.data[guild_id]['role'][role_id]['tag']
            except KeyError:
                return None

    # 获取一个服务器中全部已注册在机器人数据库中的角色id
    async def get_roles(self, guild_id) -> Union[dict, None]:
        await self.read_data()
        async with self.action_lock:
            try:
                return self.data[guild_id]['role']
            except KeyError:
                return None

    # 设置服务器角色信息
    async def try_set_role_tag(self, guild_id, role_tag, role_id) -> Union[bool, None]:
        await self.check_guild(guild_id)
        async with self.action_lock:
            if 'role' not in self.data[guild_id]:
                self.data[guild_id]['role'] = {}
            # 注册新角色数据
            if role_id not in self.data[guild_id]['role']:
                self.data[guild_id]['role'][role_id] = {'tag': [role_tag], 'permission': []}
                return True
            elif role_tag not in self.data[guild_id]['role'][role_id]['tag']:
                self.data[guild_id]['role'][role_id]['tag'].append(role_tag)
                await self.save_data()
                return True
            else:
                return None

    async def try_remove_role_tag(self, guild_id, role_tag, role_id) -> Union[bool, None]:
        await self.check_guild(guild_id)
        async with self.action_lock:
            if 'role' not in self.data[guild_id]:
                return None
            if role_id not in self.data[guild_id]['role']:
                return None
            if isinstance(self.data[guild_id]['role'][role_id]['tag'], list) and role_tag in \
                    self.data[guild_id]['role'][role_id]['tag']:
                self.data[guild_id]['role'][role_id]['tag'].remove(role_tag)
                await self.save_data()
                return True
            else:
                return None
    # 设置服务器同时最多有多少服务单
    async def set_max_ticket(self, guild_id, maxium_ticket: int) -> bool:
        await self.check_guild(guild_id)
        async with self.action_lock:
            try:
                self.data[guild_id]['max'] = maxium_ticket
                return True
            except KeyError as e:
                logging.warning('Trying assign max ticket limit to an empty guild.')
                logging.warning(f'[Args] guild_id: {guild_id}, maxium_ticket: {maxium_ticket}')
                return False

    # 从某个服务器申请服务单
    async def apply(self, guild_id, user_id) -> Union[int, None]:
        async with self.action_lock:
            user_guild_cnt = await user_service.get_guild_cnt(user_id, guild_id)

            # 检查是否达到单人开票数量最大张数，如果达到了就不开。
            # 如果未设置最大开票张数，默认为2
            if 'max' not in self.data[guild_id]:
                self.data[guild_id]['max'] = 2

            # 如果超出单人开票张数限制
            if self.data[guild_id]['max'] <= user_guild_cnt:
                return None

            await user_service.open(user_id, guild_id)
            self.data[guild_id]['cnt'] += 1
            with open(PATH.GUILD_DATA, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            return self.data[guild_id]['cnt']

    # 释放某个服务器的服务单
    async def close(self, guild_id, user_id):
        async with self.action_lock:
            await user_service.close(user_id, guild_id)

    # #####################################################################################
    # 下面是为了动态更新服务单数据新增的功能，暂时没用
    # #####################################################################################

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


# py是天生的单例模式
guild_service = GuildServiceImpl()

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
