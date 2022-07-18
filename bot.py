# -*- encoding: utf-8 -*-
'''
@File    :   bot.py    
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/8 11:32   ishgrina   1.0         None
'''

# import lib
import json
import logging
import time

from datetime import datetime, timedelta

from khl import Bot, Message, MessageTypes, EventTypes, User, Event
from khl.card import CardMessage, Card, Module, Element, Types, Struct

from py.ticket_controller import *
from py.value import AUTH

# Global

master_id = '859596959'

# Load Configuration
with open('cfg/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Bot Initialization
bot = Bot(token=config['token'])


# 鉴权模块
# #############################################################################
async def auth(user: Union[User, str], guild: Union[Guild, None] = None) -> int:
    user_id = user.id if isinstance(user, User) else user
    manager = await GuildService.get_instance()
    staff = await manager.get_role(guild.id, 'staff')
    user_authority = 0
    if guild is not None:
        g_user = await guild.fetch_user(user_id)
        roles = await guild.fetch_roles()
        # 先检查是不是管理员
        for role in roles:
            if role.has_permission(0) and role.id in g_user.roles:
                # 是管理员， 标记身份并结束循环
                user_authority |= AUTH.ADMIN
                break
        # 再检查是不是员工
        # 服务器中角色列表是一个long long数组。
        for role in g_user.roles:
            if role == staff.id:
                # 是员工，标记身份并结束循环
                user_authority |= AUTH.STAFF
                break
    return user_authority


# 封装的鉴权函数
async def check_authority(msg: Message, level: int = 1) -> bool:
    if level & await auth(msg.author, msg.ctx.guild):
        return True
    await msg.reply('你没有权限使用这个命令。')
    return False


# #############################################################################
# 指令模块
# #############################################################################
# 发送可以创建Ticket的消息
@bot.command(name='setup')
async def setupTicketBot(msg: Message):
    if not await check_authority(msg, AUTH.STAFF):
        return
    cm = CardMessage()
    cd = Card(Module.Header('点击下方按钮创建一张Ticket'),
              Module.ActionGroup(
                  Element.Button('Create Ticket!', 'create_ticket', Types.Click.RETURN_VAL)
              )
              )
    cm.append(cd)
    await msg.ctx.channel.send(cm)


# 设置服务器角色
@bot.command(name='setrole')
async def selectRole(msg: Message, rolename: str):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    roles = await msg.ctx.guild.fetch_roles()
    cm = CardMessage()
    cd = Card(Module.Header('选择' + rolename + '角色'))
    for role in roles:
        cd.append(Module.ActionGroup(
            Element.Button(role.name, 'setRole_' + rolename + '_' + str(role.id), Types.Click.RETURN_VAL)
        ))
    cm.append(cd)
    await msg.ctx.channel.send(cm)
    return


# 静音用户（设置为静音角色）
@bot.command(name='mute')
async def mute(msg: Message, username: str, contains: str, reason: str):
    if not await check_authority(msg, AUTH.STAFF):
        return
    manager = await GuildService.get_instance()
    mute_role = await manager.get_role(msg.ctx.guild.id, 'mute')
    if mute_role is None:
        await msg.ctx.channel.send(CardMessage(Card(
            Module.Header('错误'),
            Module.Section('没有设置Mute角色')
        )), temp_target_id=msg.author.id)
        return
    users = await msg.ctx.guild.list_user(msg.ctx.channel)
    for user in users:
        if user.username == username:

            await msg.ctx.guild.grant_role(user, mute_role)
            return


# 取消静音用户（移除静音角色）
@bot.command(name='unmute')
async def unmute(msg: Message, username: str):
    if not await check_authority(msg, 2):
        return
    manager = await GuildService.get_instance()
    mute_role = await manager.get_role(msg.ctx.guild.id, 'mute')
    if mute_role is None:
        await msg.ctx.channel.send(CardMessage(Card(
            Module.Header('错误'),
            Module.Section('没有设置Mute角色')
        )), temp_target_id=msg.author.id)
        return
    users = await msg.ctx.guild.list_user(msg.ctx.channel)
    for user in users:
        if user.username == username:
            await msg.ctx.guild.revoke_role(user, mute_role)
            return


# Manual
@bot.command()
async def man(msg: Message, cmd: str = ''):
    if not check_authority(msg, 2):
        return
    await manual(msg, cmd)


@bot.command(name='clean')
async def clean_user(msg: Message, user_id: str):
    if not check_authority(msg, 1):
        return
    user_service = await UserService.get_instance()
    await user_service.reset(user_id, msg.ctx.guild.id)
    await msg.reply('已清除用户' + user_id + '的数据。', is_temp=True)


#############################################################################################
# 事件处理模块
# #########################################################################################

@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def btnclk(b: Bot, event: Event):
    logging.info('event received... body is:\n\t' + str(event.body))
    if event.body['value'] == 'create_ticket':
        await create_ticket(b, event)
        return
    # 处理关闭ticket的事件, 关闭的信息开头为closeTicket_
    elif event.body['value'].startswith('closeTicket_'):
        args = event.body['value'].split('_')
        await close_ticket(b, event, args[1], args[2])
        return
    # 对第一次按钮点击做询问
    elif event.body['value'].startswith('preCloseTicket_'):
        args = event.body['value'].split('_')
        await pre_close_ticket(b, event, args[1], args[2])
        return

    # 查询消息发送的服务器
    guild = await b.fetch_guild(event.body['guild_id'])
    # 下列为高权限操作
    # 对员工开放操作
    # 鉴权
    if 1 & await auth(event.body['user_id'], guild):
        channel = await b.fetch_public_channel(event.body['target_id'])
        await channel.send("您没有权限进行此操作", temp_target_id=event.body['user_id'])
        return

    # 对管理员开放的操作
    # 鉴权
    if 2147483648 & await auth(event.body['user_id'], guild):
        channel = await b.fetch_public_channel(event.body['target_id'])
        await channel.send("您没有权限进行此操作", temp_target_id=event.body['user_id'])
        return
    if event.body['value'].startswith('setRole_'):
        args = event.body['value'].split('_')
        await set_role(b, event, args[1], args[2])
    return


# 测试指令
@bot.command(name='hello')
async def world(msg: Message):
    await msg.reply('world!')


logging.basicConfig(level='INFO')
bot.run()

# await channel.update_permission(user, allow=(2048 | 4096))
