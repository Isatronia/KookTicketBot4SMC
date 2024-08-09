# -*- encoding: utf-8 -*-
'''
@File    :   mute_controller.py    
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/17 10:25   ishgrina   1.0         None
'''
import asyncio
# import lib
import logging
import threading

import time
from khl import Bot, Message, User
from khl.card import CardMessage, Card, Module
from .guild_service import guild_service
from .mute_service import mute_service
from .value import ROLE

log = logging.getLogger(__name__)

async def mute_user(msg: Message, user: User, mute_time: int, reason: str):
    # 为用户设置禁言角色并且私聊发送原因
    # 获取禁言角色
    muted_roles = await guild_service.get_role_by_tag(msg.ctx.guild.id, ROLE.MUTE)

    # 设置禁言时间
    mute_time = time.time() + mute_time

    # 为用户设置禁言角色
    await mute_service.mute(msg.ctx.guild.id, user.id, mute_time)
    await msg.ctx.guild.grant_role(user, muted_roles[0])
    await user.send('你因为 ' + reason + ' 已被禁言，如有疑问请私聊管理。')


async def unmute_user(msg: Message, user: User):
    # 为用户解除禁言角色并且私聊发送原因
    # 获取禁言角色
    muted_roles = await guild_service.get_role_by_tag(msg.ctx.guild.id, ROLE.MUTE)
    # 错误检测
    if muted_roles is None or len(muted_roles) == 1:
        await msg.ctx.channel.send(CardMessage(Card(
            Module.Header('Error occurred'),
            Module.Section('还没有设置Mute角色啊 kora!!')
        )), temp_target_id=msg.author.id)
        return
    # 为用户解除禁言角色
    await msg.ctx.guild.revoke_role(user, muted_roles[0])
    await user.send('你已被解除禁言。')
    await mute_service.unmute(msg.ctx.guild.id, user.id)


async def check_all(bot: Bot):
    log.info('mute service started, timestamp is :' + str(time.time()))
    records = await mute_service.check()
    for rec in records:
        user_id = rec['user_id']
        guild_id = rec['guild_id']
        guild = await bot.client.fetch_guild(guild_id)
        user = await bot.client.fetch_user(user_id)
        roles = await guild_service.get_role_by_tag(guild_id, ROLE.MUTE)
        try:
            await mute_service.unmute(user_id, guild_id)
            await guild.revoke_role(user, roles[0])
        except Exception as e:
            log.error(e)
            log.error('unmute user failed, user_id is ' + str(user_id))
            continue

async def unmute_user_from_guild(bot: Bot, user_id, guild_id):
    mute_role = await guild_service.get_role_by_tag(guild_id, ROLE.MUTE)
    guild = await bot.client.fetch_guild(guild_id)
    try:
        await mute_service.unmute(user_id, guild_id)
        await guild.revoke_role(user_id, mute_role[0])
    except Exception as e:
        log.error(e)
        log.error('unmute user failed, user_id is ' + str(user_id))


def mute_suspend(bot: Bot, start_signal: threading.Event):
    log.info(f"Mute suspend thread loaded. Event status is {start_signal.is_set()}")
    try:
        start_signal.wait()
        log.info(f"Mute service thread started.")
        while True and start_signal.is_set():
            next_time = mute_service.query_nearest_unmute_user()
            if next_time is not None and time.time() >= next_time[0]:
                fea = asyncio.run_coroutine_threadsafe(
                    unmute_user_from_guild(bot, next_time[2], next_time[1]),
                    bot.loop)
                try:
                    result = fea.result(timeout=30)
                except TimeoutError:
                    log.warning(f"Unmute action time out, canceled.")
                    fea.cancel()
                except BaseException as e:
                    log.error(e)
    except KeyboardInterrupt:
        return
