# -*- encoding: utf-8 -*-
'''
@File    :   user_service.py
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2024/4/25 20:02   ishgrina   1.0         None
'''
import asyncio
from datetime import datetime
import heapq
import logging
import os
import threading
from logging.handlers import TimedRotatingFileHandler
from typing import Union

from khl import User, Guild, Message, Event, Bot

from .value import ROLE, AUTH

master_id = '859596959'


# #############################################################################
# 功能函数
# #############################################################################

class PriorityQueue:
    def __init__(self):
        self._heap = []
        self._write_lock = threading.Lock()

    def put(self, item):
        with self._write_lock:
            heapq.heappush(self._heap, item)

    def push(self, item):
        self.put(item)

    def peek(self):
        return self._heap[0] if self._heap else None

    def pop(self):
        with self._write_lock:
            return heapq.heappop(self._heap) if self._heap else None

    def is_empty(self):
        return not self._heap

    def delete(self, item):
        with self._write_lock:
            self._heap.remove(item)

    def __str__(self):
        return str(self._heap)


# #############################################################################
# 功能函数模块
# #############################################################################

def get_formatted_date() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# #############################################################################
# 鉴权模块
# #############################################################################

# 封装的鉴权函数
async def check_authority(msg: Message, level: int = 1) -> bool:
    # 用于Dev紧急维护
    if msg.author.id == master_id:
        return True
    userAuth = await getUserGuildAuthority(msg.author, msg.ctx.guild)
    if level & userAuth != 0:
        return True
    await msg.reply('你没有权限使用这个命令。')
    return False


async def has_role(role: str = None, msg: Message = None, event: Event = None, b: Bot = None) -> bool:
    # 先检测角色是否为空，为空直接返回
    if role is None:
        return False

    # msg模式，通过msg确定用户和角色
    if msg is not None:
        if msg.author.id == master_id:
            return True
        roles = msg.ctx.guild.fetch_roles()
        for r in roles:
            if r.name == role and r.id in msg.author.roles:
                return True
        return False

    # 事件模式，通过事件获取用户和角色
    elif event is not None and b is not None:
        user_id = event.body['user_id']
        if user_id == master_id:
            return True
        guild = await b.client.fetch_guild(event.body['guild_id'])
        roles = await guild.fetch_roles()
        user = await guild.fetch_user(user_id)
        for r in roles:
            if r.name == role and r.id in user.roles:
                return True
        return False
        # roles = event.body.


async def getUserGuildAuthority(user: Union[User, str], guild: Union[Guild, None] = None) -> int:
    # 局部引用，试试看
    # 2024-4-26 成了
    from .guild_service import guild_service

    # 先拿到用户的str型id
    user_id = user.id if isinstance(user, User) else user
    user_id = str(user_id)

    # 从配置文件抓取服务器员工id
    staff = await guild_service.get_role_by_tag(guild.id, ROLE.STAFF)
    staff = None if staff is None else list(map(int, staff))

    # 开始鉴权,初始化参数
    user_authority = 0

    # 开发人员维护用，给予全部机器人操作权限
    # 紧急时关停一些功能使用
    if master_id == user_id:
        for x in filter(lambda x: not x[0].startswith('__'), vars(AUTH).items()):
            user_authority |= x[1]
        return user_authority

    # 如果服务器非空，开始查找用户角色
    if guild is not None:
        g_user = await guild.fetch_user(user_id)
        roles = await guild.fetch_roles()

        # 先检查是不是管理员
        for role in roles:
            if role.has_permission(0) and role.id in g_user.roles:
                # 是管理员， 标记身份并返回
                user_authority |= AUTH.ADMIN
                user_authority |= AUTH.STAFF
                return user_authority

        # 再检查是不是员工
        # 服务器中角色列表是一个long long数组。
        if staff is not None:
            for role in g_user.roles:
                if role in staff:
                    # 是员工，标记身份并结束循环
                    user_authority |= AUTH.STAFF
                    break
    return user_authority


# 鉴权的装饰器，试试新玩意
def CheckAuth(auth: int = 0):
    async def decorator_auth(func):
        async def wrapper(*args, **kwargs):
            if not asyncio.iscoroutinefunction(func):
                raise TypeError("This decorator must use on coroutine func.")
            user_id = None
            user_auth = None
            cnl = None
            try:
                # 如果是普通消息，获取用户信息和服务器信息
                # 此时 args[0] 是Message
                if args and isinstance(args[0], Message):
                    user_auth = await getUserGuildAuthority(args[0].author, args[0].ctx.guild)
                    cnl, user_id = args[0].ctx.channel, args[0].author

                # 如果是事件触发，获取用户权限
                # 此时 args[0] 是bot, args[1] 是Event
                elif args and isinstance(args[1], Event):
                    # 查询消息发送的服务器,并获取用户权限
                    guild = await args[0].client.fetch_guild(args[1].body['guild_id'])
                    user_auth = await getUserGuildAuthority(args[1].body['user_id'], guild)
                    cnl, user_id = await args[0].client.fetch_public_channel(args[1].body['target_id']), args[1].body[
                        'user_id']
                    pass
            except IndexError as e:
                pass

            if user_auth is not None:
                if user_auth & auth == 0:
                    await cnl.send("您没有权限进行此操作", temp_target_id=user_id)
                    return None
            return await func(*args, **kwargs)

        return wrapper

    return decorator_auth
