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
import random

from khl import EventTypes

from py.ticket_controller import *
from py.mute_controller import *
from py.value import AUTH, ROLE, get_time
from py.parser import *
from py.manul_controller import manual

# Global

master_id = '859596959'

# Load Configuration
with open('cfg/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Bot Initialization
bot = Bot(token=config['token'])


# #############################################################################
# 鉴权模块
# #############################################################################
async def auth(user: Union[User, str], guild: Union[Guild, None] = None) -> int:
    user_id = user.id if isinstance(user, User) else user

    staff = await guild_service.get_role(guild.id, ROLE.STAFF)
    user_authority = 0
    if master_id == user_id:
        for x in filter(lambda x: not x[0].startswith('__'), vars(AUTH).items()):
            user_authority |= x[1]
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
        if staff is not None:
            for role in g_user.roles:
                if role == int(staff):
                    # 是员工，标记身份并结束循环
                    user_authority |= AUTH.STAFF
                    break
    return user_authority


# 封装的鉴权函数
async def check_authority(msg: Message, level: int = 1) -> bool:
    # 用于Dev紧急维护
    if msg.author.id == master_id:
        return True
    if level & await auth(msg.author, msg.ctx.guild) != 0:
        return True
    await msg.reply('你没有权限使用这个命令。')
    return False


async def log(o):
    logging.info(get_time() + ' ' + str(o))


# #############################################################################
# 指令模块
# #############################################################################
# 发送可以创建Ticket的消息
@bot.command(name='setup')
async def setupTicketBot(msg: Message, role: str = 'staff'):
    await log('setting up ticket generator... role is:' + role)
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    if await guild_service.get_role(msg.ctx.guild.id, role) is None:
        await log('role not set, process end.')
        await msg.reply('还没有设定' + role + '角色', is_temp=True)
        return
    cm = CardMessage()
    cd = Card(Module.Header(Element.Text('点击下方按钮创建一张只有 {:} 能看到的Ticket'.format(role))),
              Module.ActionGroup(
                  Element.Button('Create Ticket!', 'create_ticket_' + role, Types.Click.RETURN_VAL)
              )
              )
    cm.append(cd)
    await msg.ctx.channel.send(cm)
    await log('Generator create succeed.')


# 设置服务器角色
@bot.command(name='setrole')
async def selectRole(msg: Message, rolename: str):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    await log('setting role: ' + rolename + 'at guild ' + msg.ctx.guild.name + ' guild id is: ' + msg.ctx.guild.id)
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

@bot.command(name='listrole')
async def listrole(msg: Message):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    await log('listting role...')
    roles = await guild_service.get_roles(msg.ctx.guild.id)
    cm = CardMessage()
    cd = Card(Module.Header('当前所有角色为:'))
    for k in roles:
        cd.append(Module.Section(Element.Text(content=k, type=Types.Text.KMD)))
    cm.append(cd)
    await msg.reply(cm)



# 静音用户（设置为静音角色）
@bot.command(name='mute')
async def mute(msg: Message, userid: str, contains: str, reason: str):

    # Log
    await log('trying mute: ' + userid + ' ' + contains + ' for ' + reason)

    # 鉴权
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        logging.info(get_time() + 'Unauthorized, mute action rejected.')
        return

    # Log
    await log(
        'Authorized. begin mute process mute' + userid + ' in guild' + msg.ctx.guild.name + '(id is: ' + msg.ctx.guild.id + ')')

    # 检查静音用户是否存在，并设置静音角色 （Tag）
    mute_role = await guild_service.get_role(msg.ctx.guild.id, ROLE.MUTE)
    # 错误检测，没有设置静音角色（Tag）
    if mute_role is None:
        logging.debug(get_time() + 'mute role not found. cur data is : + \n' + str(guild_service.data))
        await msg.ctx.channel.send(CardMessage(Card(
            Module.Header('Error occurred'),
            Module.Section('还没有设置Mute角色啊 kora!!')
        )), temp_target_id=msg.author.id)
        return

    try:
        time = await timeParser(contains)
    except Exception as e:
        await msg.reply(str(e), is_temp=True)
        await msg.reply('出错啦，请检查错误信息=w=', is_temp=True)

    logging.info(get_time() + 'mute time resolved: ' + str(time))
    await mute_user(bot, msg, await bot.client.fetch_user(userid), time, reason)
    logging.info(get_time() + 'muted' + userid + ' ' + contains + ' for ' + reason)


# 取消静音用户（移除静音角色）
@bot.command(name='unmute')
async def unmute(msg: Message, userid: str):

    # 鉴权
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return

    # log
    await log('unmute user ' + userid + ' at ' + msg.ctx.guild.name + '(id is {:} )'.format(msg.ctx.guild.id))

    # 获取静音用户
    mute_role = await guild_service.get_role(msg.ctx.guild.id, ROLE.MUTE)

    # 错误检测
    if mute_role is None:
        await msg.ctx.channel.send(CardMessage(Card(
            Module.Header('Error occurred'),
            Module.Section('还没有设置Mute角色啊 kora!!')
        )), temp_target_id=msg.author.id)
        return

    # 获取用户
    user = await bot.client.fetch_user(userid)

    try:
        await unmute_user(bot, msg, user)
    except Exception as e:
        await log(str(e))
        await msg.reply(str(e), is_temp=True)
        await msg.reply('出错啦，请检查错误信息=w=', is_temp=True)

    return


# Manual
@bot.command()
async def man(msg: Message, cmd: str = ''):
    if not check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    await manual(msg, cmd)


# clean user Record
@bot.command(name='clean')
async def clean_user(msg: Message, user_id: str):
    if not check_authority(msg, AUTH.ADMIN):
        return
    await log('cleaning user data: {:} at {:}(id is: {:})'.format(user_id, msg.ctx.guild.name, msg.ctx.guild.id))
    await user_service.reset(user_id, msg.ctx.guild.id)
    await msg.reply('已清除用户' + user_id + '的数据。', is_temp=True)


# update Channel name
@bot.command(name='rename')
async def rename(msg: Message, name: str):
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    await log('rename channel id {:} as {:}'.format(msg.ctx.channel.id, name))
    try:
        await msg.ctx.channel.update(name=name)
        await msg.reply('重命名成功=w=。', is_temp=True)
    except Exception as e:
        await msg.reply(str(e), is_temp=True)
        await msg.reply('出错啦，请检查错误信息=w=', is_temp=True)


@bot.command(name='dice')
async def dice(msg:Message, mx: int):
    res = random.randint(1, mx)
    await msg.reply("骰子结果是：{:}".format(res))
    await log(str(msg.author.nickname) + '投了个骰子，结果是:' + str(res))

#############################################################################################
# 事件处理模块
# #########################################################################################

@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def btnclk(b: Bot, event: Event):
    async def check_auth(user_auth, auth):
        if (auth & user_auth) != auth:
            channel = await b.client.fetch_public_channel(event.body['target_id'])
            await channel.send("您没有权限进行此操作", temp_target_id=event.body['user_id'])
            return False
        return True

    logging.info(get_time() + 'event received... body is:\n' + str(event.body))

    if event.body['value'].startswith('create_ticket_'):
        # check if role exists

        args = event.body['value'].split('_')
        roles = await guild_service.get_roles(event.body['guild_id'])
        if args[-1] not in roles:
            cnl = await b.client.fetch_public_channel(event.target_id)
            await cnl.send('角色未设置，请检查您的设定')
            return
        await create_ticket(b, event, args[-1])
        return

    # 关闭Ticket时对第一次按钮点击做询问
    elif event.body['value'].startswith('preCloseTicket_'):
        args = event.body['value'].split('_')
        await pre_close_ticket(b, event, args[1], args[2])
        return

    # 处理关闭ticket的事件, 关闭的信息开头为closeTicket_
    elif event.body['value'].startswith('closeTicket_'):
        args = event.body['value'].split('_')
        await close_ticket(b, event, args[1], args[2])
        return

    # 查询消息发送的服务器
    guild = await b.client.fetch_guild(event.body['guild_id'])
    # 下列为高权限操作
    user_authority = await auth(event.body['user_id'], guild)

    # 删除Ticket
    if event.body['value'].startswith('deleteTicket_'):
        logging.info('delete ticket invoked')
        if not await check_auth(user_authority, AUTH.STAFF):
            return
        cnl = await b.client.fetch_public_channel(event.body['target_id'])
        await cnl.send('Ticket已经删除，可能需要一段时间同步到您的设备。请不要重复删除')
        args = event.body['value'].split('_')
        await delete_ticket(b, event, args[1], args[2])

    # 重开Ticket
    elif event.body['value'].startswith('reopenTicket_'):
        logging.info('reopen ticket invoked')
        if not await check_auth(user_authority, AUTH.STAFF):
            return
        args = event.body['value'].split('_')
        await reopen_ticket(b, event, args[1], args[2])

    # 设置角色
    if event.body['value'].startswith('setRole_'):
        if not await check_auth(user_authority, AUTH.ADMIN):
            return
        args = event.body['value'].split('_')
        await set_role(b, event, args[1], args[2])
    return


# #########################################################################################
# 定时任务
# #########################################################################################
@bot.task.add_interval(minutes=1)
async def check():
    await check_all(bot)


# 测试指令
@bot.command(name='hello')
async def world(msg: Message, *args):
    if not await check_authority(msg, 0):
        return
    await msg.reply(' '.join(args))


logging.basicConfig(level='INFO')
bot.run()

# await channel.update_permission(user, allow=(2048 | 4096))
