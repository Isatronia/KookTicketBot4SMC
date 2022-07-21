# -*- encoding: utf-8 -*-
'''
@File    :   mute_controller.py    
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/17 10:25   ishgrina   1.0         None
'''

# import lib
import asyncio
import logging

import time
from khl import Bot, Message, Guild, User, Channel, Role
from .guild_service import GuildService
from .mute_service import MuteService
from .value import PATH, ROLE


async def mute_user(msg: Message, user: User, mute_time: int, reason: str):
    mute_service = await MuteService.get_instance()
    # 为用户设置禁言角色并且私聊发送原因

    # 获取禁言角色
    manager = await GuildService.get_instance()
    muted_role = await manager.get_role(msg.ctx.guild.id, ROLE.MUTE)

    # 设置禁言时间
    mute_time = time.time() + mute_time

    # 为用户设置禁言角色
    await msg.ctx.guild.grant_role(user, muted_role)
    await user.send('你因为 ' + reason + ' 已被禁言， 请私聊管理解禁。')
    await mute_service.mute(msg.ctx.guild.id, user.id, mute_time)


async def unmute_user(msg: Message, user: User):
    mute_service = await MuteService.get_instance()
    # 为用户设置禁言角色并且私聊发送原因

    # 获取禁言角色
    manager = await GuildService.get_instance()
    muted_role = await manager.get_role(msg.ctx.guild.id, ROLE.MUTE)

    # 为用户设置禁言角色
    await msg.ctx.guild.revoke_role(user, muted_role)
    await user.send('你已被解除禁言。')
    await mute_service.unmute(msg.ctx.guild.id, user.id)


async def check_all(bot: Bot):
    logging.info('mute service started, timestamp is :' + str(time.time()))
    mute_service = await MuteService.get_instance()
    manager = await GuildService.get_instance()
    records = await mute_service.check()
    for rec in records:
        user_id = rec['user_id']
        guild_id = rec['guild_id']
        guild = await bot.fetch_guild(guild_id)
        user = await bot.fetch_user(user_id)
        role = await manager.get_role(guild_id, ROLE.MUTE)
        try:
            await mute_service.unmute(user_id, guild_id)
            await guild.revoke_role(user, role)
        except Exception as e:
            logging.error(e)
            logging.error('unmute user failed, user_id is ' + str(user_id))
            continue


