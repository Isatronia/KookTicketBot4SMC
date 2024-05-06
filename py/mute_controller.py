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
import logging

import time
from khl import Bot, Message, User
from .guild_service import guild_service
from .mute_service import mute_service
from .value import ROLE


async def mute_user(msg: Message, user: User, mute_time: int, reason: str):
    # 为用户设置禁言角色并且私聊发送原因
    # 获取禁言角色
    muted_roles = await guild_service.get_role_by_tag(msg.ctx.guild.id, ROLE.MUTE)

    # 设置禁言时间
    mute_time = time.time() + mute_time

    # 为用户设置禁言角色
    await msg.ctx.guild.grant_role(user, muted_roles[0])
    await user.send('你因为 ' + reason + ' 已被禁言， 请私聊管理解禁。')
    await mute_service.mute(msg.ctx.guild.id, user.id, mute_time)


async def unmute_user(msg: Message, user: User):
    # 为用户解除禁言角色并且私聊发送原因
    # 获取禁言角色
    muted_roles = await guild_service.get_role_by_tag(msg.ctx.guild.id, ROLE.MUTE)

    # 为用户解除禁言角色
    await msg.ctx.guild.revoke_role(user, muted_roles[0])
    await user.send('你已被解除禁言。')
    await mute_service.unmute(msg.ctx.guild.id, user.id)


async def check_all(bot: Bot):
    logging.info('mute service started, timestamp is :' + str(time.time()))
    records = await mute_service.check()
    for rec in records:
        user_id = rec['user_id']
        guild_id = rec['guild_id']
        guild = await bot.client.fetch_guild(guild_id)
        user = await bot.client.fetch_user(user_id)
        role = await guild_service.get_role_by_tag(guild_id, ROLE.MUTE)
        try:
            await mute_service.unmute(user_id, guild_id)
            await guild.revoke_role(user, role)
        except Exception as e:
            logging.error(e)
            logging.error('unmute user failed, user_id is ' + str(user_id))
            continue


