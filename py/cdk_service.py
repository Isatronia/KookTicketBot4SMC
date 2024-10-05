#  Copyright (c) 2024.
#

'''
@File    :   cdk_service.py
@Author  :   Ishgrina
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA
@Version :   1.0
@Modify  :   8/8/2024
@Desciption
--------------------------------------

--------------------------------------
'''
import time
import uuid
from typing import Union

from .value import PATH, config
from .utils import get_formatted_date
from .parser import extract_cdk_command
from .guild_service import guild_service
from .user_service import user_service

import json
import logging
from khl import User, Guild, Message
from asyncio import Lock

'''
cdk.json - 记录cdk和激活历史
    "cdk" - uuid表示的cdk,用于全局唯一检索
        command -  cdk被激活时使用的指令
        activated - cdk被谁激活
            id - kook用户id
            name - 激活时的kook用户名
        created - 该cdk是被谁创建的
            id - kook用户id
            name - 创建者创建时的kook用户名
'''

log = logging.getLogger(__name__)


class ActivateTooFastError(Exception):
    def __init__(self, info: str = None):
        super().__init__(info)
        pass

    pass


class Actions:

    def __init__(self):
        pass

    async def grant(self, msg: Message, *args):
        roles = await msg.ctx.guild.fetch_roles()
        for r in roles:
            if r.name == args[0]:
                await msg.ctx.guild.grant_role(msg.author, r)
        return


class CdkServiceImpl:
    _data: dict = {}
    _flock: Lock = Lock()
    _actions: Actions = Actions()

    def __init__(self):
        self._load()
        pass

    def _get_data(self):
        return CdkServiceImpl._data

    def _load(self):
        try:
            with open(PATH.CDK_PATH, 'r', encoding='utf-8') as f:
                CdkServiceImpl._data = json.load(f)
                pass
        except FileNotFoundError:
            log.error(
                "Guild data file is not existed. Please check if it's not the first time running this program.")
            CdkServiceImpl._data = {}

    def _store(self):
        with open(PATH.CDK_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._get_data(), f, ensure_ascii=False, indent=4)

    async def check_cdk(self, cdk: str) -> bool:
        if cdk in CdkServiceImpl._data:
            return True
        else:
            return False

    async def generate_cdk(self, msg: Message, cmd: str) -> Union[str, None]:
        command = extract_cdk_command(cmd)
        if command is None:
            return None
        else:
            async with CdkServiceImpl._flock:
                cdk = str(uuid.uuid4())
                while cdk in self._get_data():
                    cdk = str(uuid.uuid4())
                self._get_data()[cdk] = {"command": cmd,
                                         "activated": None,
                                         "created": {"id": str(msg.author.id),
                                                     "name": str(msg.author.nickname),
                                                     "time": get_formatted_date()}
                                         }
                self._store()
            return cdk

    # CDK激活时间间隔检查
    async def cdk_activate_check(self, msg: Message):
        epoch = config["activate_gap"] if config["activate_gap"] is not None else 3600
        last_activate_time = await user_service.try_get_user_key(msg.author.id, msg.ctx.guild.id, "last_activate")
        try:
            if time.time() - last_activate_time <= epoch:
                raise ActivateTooFastError
        except TypeError:
            pass
        await user_service.try_set_user_key(msg.author.id, msg.ctx.guild.id, "last_activate", time.time())
        return

    # 尝试激活CDK
    async def try_activate_cdk(self, cdk, msg: Message) -> bool:
        # 检查自上次激活的时间间隔是否满足要求
        await self.cdk_activate_check(msg)
        # 检查是否已经被使用
        if cdk not in self._get_data() or self._get_data()[cdk]["activated"] is not None:
            return False
        # 执行激活代码
        async with CdkServiceImpl._flock:
            command = self._get_data()[cdk]['command'].split(' ')
            try:
                method = getattr(CdkServiceImpl._actions, command[0])
                await method(msg, *command[1:])
                CdkServiceImpl._data[cdk]["activated"] = {"id": str(msg.author.id),
                                                          "name": str(msg.author.nickname),
                                                          "time": get_formatted_date()}
                self._store()
            except BaseException as e:
                log.error(e)
                return False
            return True


cdk_service = CdkServiceImpl()
