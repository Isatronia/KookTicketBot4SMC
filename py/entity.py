# -*- encoding: utf-8 -*-
'''
@File    :   entity.py
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2024/5/6 19:37   ishgrina   1.0         Entitys using in project
'''
import json
import os
# ###############################################################
# imports
# ###############################################################
from typing import Union
from enum import Enum
from utils import get_formatted_date


# ###############################################################
# 项目中用到的实体
# ###############################################################

class TKSTAT:
    DELETED = 0
    OPEN = 1
    CLOSED = 2


class Ticket:

    def __init__(self, ticket_id: int = None, guild_id: int = None, applier: str = None, state: int = None,
                 msg_log: list = None):
        # 票的id
        self.ticket_id = ticket_id
        # 所属服务器
        self.guild_id = guild_id
        # 申请人(id 或 User)
        self.applier = applier
        # 票的状态(开启， 关闭， 删除)
        self.state = state
        # 消息记录
        self.msg_log = msg_log

    def to_dict(self):
        return {
            "ticketId": self.ticket_id,
            "guildId": self.guild_id,
            "applier": self.applier,
            "state": self.state,
            "msgLog": self.msgLog
        }

    @classmethod
    def from_dict(cls, data):
        return Ticket(data["ticketId"], data["guildId"], data["applier"], data["state"], data["msgLog"])

    @classmethod
    def load_from_file(cls, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def __str__(self):
        return f"Ticket[{self.ticket_id}] from Guild [{self.guild_id}]"

    def create(self, ticket_id: int, guild_id: int, user_id: int):
        self.ticket_id = ticket_id
        self.guild_id = guild_id
        self.applier = user_id
        self.state = TKSTAT.OPEN
        self.msg_log = []

    def load(self, path: str = None):
        if path is None:
            raise FileNotFoundError
        with open(path, 'r', encoding='utf-8') as f:
            self.from_dict(json.load(f))
        return self

    def save(self, path: str = None):
        if path is None:
            raise FileNotFoundError
        if path and not os.path.exists(path):
            os.makedirs(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4)

    def log(self, user: str, msg: str, time: str = None):
        if time is None:
            time = get_formatted_date()
        self.msg_log.append({'user': user, "time": time, "msg": msg})
