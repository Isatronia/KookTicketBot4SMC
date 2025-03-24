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
from value import PATH
from utils import get_formatted_date


# ###############################################################
# 项目中用到的实体
# ###############################################################

class TKSTAT:
    DELETED = 0
    OPEN = 1
    CLOSED = 2


class Ticket:

    def __init__(self, ticket_id: int = None, guild_id: int = None, channel_id: int = None, applier: int = None, state: int = None,
                 msg_log: list = None):
        # 票的id
        self.ticket_id = ticket_id
        # 所属服务器
        self.guild_id = guild_id
        # 频道id
        self.channel_id = channel_id
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
            "channelId": self.channel_id,
            "applier": self.applier,
            "state": self.state,
            "msgLog": self.msg_log
        }

    @classmethod
    def from_dict(cls, data):
        return Ticket(
            data["ticketId"],
            data["guildId"],
            data["channelId"],
            data["applier"],
            data["state"],
            data["msgLog"])

    # 从文件加载
    @classmethod
    def load_from_file(cls, path: str = None, guild_id: int = None, ticket_id: int = None):
        if ticket_id is not None and guild_id is not None:
            path = PATH.TICKET_DATA_DIRECTORY + f"{guild_id}\\{ticket_id}.json"
        if path is None:
            raise FileNotFoundError
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def __str__(self):
        return f"Ticket[{self.ticket_id}] from Guild [{self.guild_id}]"

    def create(self, ticket_id: int, guild_id: int, channel_id: int, user_id: int):
        self.ticket_id = ticket_id
        self.guild_id = guild_id
        self.channel_id = channel_id
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
            path = PATH.TICKET_DATA_DIRECTORY + f"\\{self.guild_id}"
        if path and not os.path.exists(path):
            os.makedirs(path)
        with open(path + f"\\{self.ticket_id}.json", 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4)

    def update(self, ticket):
        if not isinstance(ticket, Ticket):
            return
        if ticket.ticket_id is not None:
            self.ticket_id = ticket.ticket_id
        if ticket.guild_id is not None:
            self.guild_id = ticket.guild_id
        

    def log(self, user: str, msg: str, time: str = None):
        if time is None:
            time = get_formatted_date()
        self.msg_log.append({'user': user, "time": time, "msg": msg})
