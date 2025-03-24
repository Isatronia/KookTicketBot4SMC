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
from .value import PATH, config

'''
data.json - GUILD DATA
- cnt 服务器全部 Ticket 数量
- max 服务器单人最多 Ticket 数量
- role 服务器角色（自定义）
  role_id
    - name
    - permission
- channel 频道（暂时没用）
- create_ticket 哪个角色可以创建 Ticket
'''

log = logging.getLogger()


class GuildServiceImpl:
    _data: dict = {}
    action_lock: Lock = Lock()
    _flock: Lock = Lock()
    init_lock: Lock = Lock()

    # 初始化GuildService
    def __init__(self):
        self._load()

    def _get_data(self):
        return GuildServiceImpl._data

    def _load(self):
        try:
            with open(PATH.GUILD_DATA, 'r', encoding='utf-8') as f:
                GuildServiceImpl._data = json.load(f)
                pass
        except FileNotFoundError:
            log.error(
                "Guild data file is not existed. Please check if it's not the first time running this program.")
            GuildServiceImpl._data = {}

    def _store(self):
        try:
            with open(PATH.GUILD_DATA, 'w', encoding='utf-8') as f:
                json.dump(self._get_data(), f, ensure_ascii=False, indent=4)
        except Exception as e:
            log.error(str(e))

    # 把数据保存到本地文件
    async def store(self) -> None:
        async with self._flock:
            self._store()
        return None

    # 从本地文件读取数据
    async def load(self) -> None:
        async with self._flock:
            self._load()

    # 初始化服务器信息
    # 新增服务器时初始化数据
    async def init_guild(self, guild_id):
        await self.load()
        if guild_id not in self._get_data():
            async with self.init_lock:
                if guild_id not in self._get_data():
                    self._get_data()[guild_id] = {
                        'cnt': 1,       # 初始Ticket计数为1
                        'role': {},     # 服务器角色列表
                        'channel': {},  # 暂无作用
                        'config': {}    # 服务器配置项
                    }
                    await self.store()

    # 检查服务器是否在机器人的数据库中注册,如果没有就注册。
    # 用于确保访问时能够获取服务器
    async def check_guild(self, guild_id) -> None:
        async with self.action_lock:
            if guild_id not in self._get_data():
                await self.init_guild(guild_id)
        return

    # 获取服务器信息
    async def get(self, guild_id: int) -> dict:
        return self._get_data()[guild_id]

    # 设置服务器配置
    async def set_guild_config(self, guild_id: int, key: str, value: str) -> Union[bool, None]:
        try:
            log.info(f'setting config [ {key} : {value} ] in guild {guild_id}..')
            if self._data[guild_id] is None:
                await self.init_guild(guild_id)
            async with self.action_lock:
                if 'config' not in self._data[guild_id]:
                    self._data[guild_id]['config'] = {key: value}
                else:
                    self._data[guild_id]['config'][key] = value
                await self.store()
            return True
        except KeyError:
            log.warning(f"An error occurred setting config in guild {guild_id}. config is: {key} : {value}")
            return None

    # 清除服务器配置
    async def clear_guild_config(self, guild_id: int) -> Union[bool, None]:
        try:
            async with self.action_lock:
                self._data[guild_id]['config'] = {}
                await self.store()
                return True
        except KeyError:
            log.warning(f'Clear guild config failed, guild id is: {guild_id}')
        return None

    async def clear_guild_config_by_key(self, guild_id: int, key: str) -> Union[bool, None]:
        async with self.action_lock:
            try:
                log.info(f'Deleting config[{key}] in guild[{guild_id}]')
                del self._data[guild_id]['config'][key]
                await self.store()
                return True
            except KeyError:
                log.info(f'Key not exists, return.')
            return None


    async def get_guild_config(self, guild_id: int, key: str) -> Union[str, None]:
        try:
            log.info(f'Getting config {key} in guild {guild_id}')
            return self._data[guild_id]['config'][key]
        except KeyError:
            log.warning(f'Config not found.')
        return None

    async def list_guild_config(self, guild_id: int) -> Union[str, None]:
        try:
            log.info(f"Listing guild[{guild_id}] config")
            async with self.action_lock:
                return json.dumps(self._data[guild_id]['config'], indent=4)
        except KeyError:
            log.warning(f'Guild{guild_id} or its config not exist.')

    # 根据角色名,获取已注册在机器人数据库中的服务器的角色信息
    async def get_role_by_tag(self, guild_id: int, role_tag: str) -> Union[list, None]:
        await self.load()
        async with self.action_lock:
            matching_ids = []
            try:
                d = self._get_data()[guild_id]['role']
                for role_id in d:
                    if 'tag' in d[role_id] and role_tag in d[role_id]['tag']:
                        matching_ids.append(role_id)
                # return self.data[guild_id]['role'][role_name]
            except KeyError:
                return None
            if len(matching_ids) == 0:
                log.warning(f"Finding role {role_tag} in {guild_id} but not found. Return None.")
                return None
                # raise KeyError("Role Not Found")
            return matching_ids

    async def get_tag_by_role_id(self, guild_id, role_id: int) -> Union[None, list]:
        await self.load()
        async with self.action_lock:
            try:
                if role_id in self._get_data()[guild_id]['role']:
                    return self._get_data()[guild_id]['role'][role_id]['tag']
            except KeyError:
                return None

    # 获取一个服务器中全部已注册在机器人数据库中的角色id
    async def get_roles(self, guild_id) -> Union[dict, None]:
        await self.load()
        async with self.action_lock:
            try:
                return self._get_data()[guild_id]['role']
            except KeyError:
                return None

    # 设置服务器角色信息
    async def try_set_role_tag(self, guild_id, role_tag, role_id) -> Union[bool, None]:
        await self.check_guild(guild_id)
        async with self.action_lock:
            if 'role' not in self._get_data()[guild_id]:
                self._get_data()[guild_id]['role'] = {}
            # 注册新角色数据
            if role_id not in self._get_data()[guild_id]['role']:
                self._get_data()[guild_id]['role'][role_id] = {'tag': [role_tag], 'permission': []}
                await self.store()
                return True
            elif role_tag not in self._get_data()[guild_id]['role'][role_id]['tag']:
                self._get_data()[guild_id]['role'][role_id]['tag'].append(role_tag)
                await self.store()
                return True
            else:
                return None

    async def try_remove_role_tag(self, guild_id, role_tag, role_id) -> Union[bool, None]:
        await self.check_guild(guild_id)
        async with self.action_lock:
            if 'role' not in self._get_data()[guild_id]:
                return None
            if role_id not in self._get_data()[guild_id]['role']:
                return None
            if isinstance(self._get_data()[guild_id]['role'][role_id]['tag'], list) and role_tag in \
                    self._get_data()[guild_id]['role'][role_id]['tag']:
                self._get_data()[guild_id]['role'][role_id]['tag'].remove(role_tag)
                await self.store()
                return True
            else:
                return None

    # 设置服务器同时最多有多少服务单
    async def set_max_ticket(self, guild_id, maxium_ticket: int) -> bool:
        await self.check_guild(guild_id)
        async with self.action_lock:
            try:
                self._get_data()[guild_id]['max'] = maxium_ticket
                return True
            except KeyError as e:
                log.warning('Trying assign max ticket limit to an empty guild.')
                log.warning(f'[Args] guild_id: {guild_id}, maxium_ticket: {maxium_ticket}')
                return False

    # 申请Ticket前进行的数量检查，测试是否超出单人申请上限
    async def apply_ticket(self, guild_id, user_id) -> Union[int, None]:
        async with self.action_lock:
            # 检查是否达到单人开票数量最大张数，如果达到了就不开。
            user_guild_cnt = await user_service.get_guild_cnt(user_id, guild_id)

            # 如果未设置最大开票张数，默认为2
            if 'max' not in self._get_data()[guild_id]:
                temp_ticket_max_count = 2
                self._get_data()[guild_id]['max'] = 2 if config['default_ticket_number'] is None else config[
                    'default_ticket_number']

                # 如果超出单人开票张数限制
            if self._get_data()[guild_id]['max'] <= user_guild_cnt:
                return None

            await user_service.open(user_id, guild_id)
            self._get_data()[guild_id]['cnt'] += 1
            with open(PATH.GUILD_DATA, 'w', encoding='utf-8') as f:
                json.dump(self._get_data(), f, ensure_ascii=False, indent=4)
            return self._get_data()[guild_id]['cnt']

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
            await self.load()
            try:
                return self._get_data()[guild_id]['channel'][channel_tag]
            except KeyError:
                return None

    # 设置服务器频道信息
    async def set_channel(self, guild_id, channel_tag, channel_id):
        await self.check_guild(guild_id)
        async with self.action_lock:
            if 'channel' not in self._get_data()[guild_id]:
                self._get_data()[guild_id]['channel'] = {}
            self._get_data()[guild_id]['channel'][channel_tag] = channel_id
            await self.store()


# py是天生的单例模式
guild_service = GuildServiceImpl()
