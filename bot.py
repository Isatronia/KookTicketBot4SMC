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
import os
import random
import signal
import sys
import threading

# import khl.py
from khl import Bot, Message, Event, EventTypes
from khl.card import CardMessage, Card, Module, Element, Types, Struct

# import coded scripts.
import py.ticket_controller as ticket_controller
from py.guild_service import guild_service
from py.mute_service import mute_service
from py.mute_controller import mute_user, unmute_user, check_all
from py.parser import timeParser, get_time, extract_ticket_prefix
from py.user_service import user_service
from py.utils import check_authority, getUserGuildAuthority
from py.value import AUTH, ROLE

# from py.manual_controller import manual

# #############################################################################
# 初始化程序代码
# #############################################################################

# 设置程序的工作路径
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 加载配置文件
with open('cfg/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

mute_observer = threading.Thread()

# 全局变量定义
# 初始化机器人
bot = Bot(token=config['token'])


@bot.on_startup
async def creator():
    return


@bot.on_shutdown
async def destructor():
    await shutdown()


async def shutdown():
    await user_service.store()
    await guild_service.store()
    await mute_service.store()


# #############################################################################
# 指令模块
# #############################################################################
# 发送可以创建Ticket的消息
@bot.command(name='setup')
async def setup_ticket_bot(msg: Message, role: str = 'staff'):
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    await ticket_controller.setup_ticket_generator(bot, msg, role)


# 设置服务器角色
@bot.command(name='setrole', aliases=['sr', 'settag'])
async def set_role(msg: Message, rolename: str, role_id: int = None):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    if role_id is not None:
        pass
    logging.info('setting role: ' + rolename + 'at guild ' + msg.ctx.guild.name + ' guild id is: ' + msg.ctx.guild.id)
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


@bot.command(name='delrole', aliases=['dr', 'deletetag'])
async def del_role(msg: Message, rolename: str):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    logging.info(f"deleting role: {rolename} at guild {msg.ctx.guild.name} witch id is: {msg.ctx.guild.id}")
    roles = await msg.ctx.guild.fetch_roles()
    cm = CardMessage()
    cd = Card(Module.Header(f'选择角色删除它们的"{rolename}"tag'))
    for role in roles:
        cd.append(Module.ActionGroup(
            Element.Button(role.name, 'delRole_' + rolename + '_' + str(role.id), Types.Click.RETURN_VAL)
        ))
    cm.append(cd)
    await msg.ctx.channel.send(cm)
    return


# Debug功能，显示当前服务器的所有已在数据库中注册的角色信息
@bot.command(name='listrole')
async def list_role(msg: Message):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    logging.info('listting role...')
    roles = await guild_service.get_roles(msg.ctx.guild.id)
    cm = CardMessage()
    if roles is None:
        cd = Card(Module.Header('当前服务器尚未设置角色信息'))
        cm.append(cd)
        await msg.reply(cm)
        return
    cd = Card(Module.Header('[DEBUG]当前所有角色为:'))
    cd.append(
        Module.Section(
            Struct.Paragraph(
                2,
                Element.Text("ID", type=Types.Text.KMD),
                Element.Text("TAG", type=Types.Text.KMD)
            )
        )
    )
    for k in roles:
        # cont = f"ID: [{k}] - TAG: [{roles[k]['tag']}]"
        # cd.append(Module.Section(Element.Text(content=cont, type=Types.Text.KMD)))
        cd.append(
            Module.Section(
                Struct.Paragraph(
                    2,
                    Element.Text(f"{k}", type=Types.Text.KMD),
                    Element.Text(f"{roles[k]['tag']}", type=Types.Text.KMD)
                )
            )
        )
    cm.append(cd)
    await msg.reply(cm)


# 静音用户（设置为静音角色）
@bot.command(name='mute')
async def mute(msg: Message, user_id: str, mute_time: str, reason: str):
    # Log
    logging.info('trying mute: ' + user_id + ' ' + mute_time + ' for ' + reason)

    # 获取用户对象
    user_obj = await bot.client.fetch_user(user_id)

    # 鉴权
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        logging.info(get_time() + 'Unauthorized, mute action rejected.')
        return

    # Log
    logging.info(
        'Authorized. begin mute process， muting' + user_id + ' in guild' + msg.ctx.guild.name + '(id is: ' + msg.ctx.guild.id + ')')

    # 检查静音用户是否存在，并设置静音角色 （Tag）
    mute_role = await guild_service.get_role_by_tag(msg.ctx.guild.id, ROLE.MUTE)

    # 错误检测，没有设置静音角色（Tag）
    if mute_role is None:
        logging.warning(get_time() + 'mute role not found. cur data is : + \n' + str(guild_service._data))
        await msg.ctx.channel.send(CardMessage(Card(
            Module.Header('Error occurred'),
            Module.Section('还没有设置Mute角色啊 kora!!')
        )), temp_target_id=msg.author.id)
        return

    try:
        mute_time = await timeParser(mute_time)
        logging.info(get_time() + 'mute time resolved: ' + str(mute_time))
        # 实现禁言
        await mute_user(msg, user_obj, mute_time, reason)
    except Exception as e:
        logging.info(str(e))
        # await msg.reply(str(e), is_temp=True)
        await msg.reply('出错啦，请联系管理员检查错误信息=w=', is_temp=True)
    logging.info(get_time() + f"succeed muted {user_id} {mute_time} for {reason}")


# 取消静音用户（移除静音角色）
@bot.command(name='unmute')
async def unmute(msg: Message, userid: str):
    # 鉴权
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return

    # log
    logging.info('unmute user ' + userid + ' at ' + msg.ctx.guild.name + '(id is {:} )'.format(msg.ctx.guild.id))

    # 获取用户
    user = await bot.client.fetch_user(userid)

    try:
        await unmute_user(msg, user)
    except Exception as e:
        logging.error(str(e))
        await msg.reply(str(e), is_temp=True)
        await msg.reply('出错啦，请检查错误信息=w=', is_temp=True)

    return


# Manual
@bot.command(name='man')
async def man(msg: Message, cmd: str = ''):
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    await ticket_controller.manual(msg, cmd)


# clean user Record
@bot.command(name='clean')
async def clean_user_data(msg: Message, user_id: str):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    logging.info('cleaning user data: {:} at {:}(id is: {:})'.format(user_id, msg.ctx.guild.name, msg.ctx.guild.id))
    await user_service.reset(user_id, msg.ctx.guild.id)
    await msg.reply('已清除用户' + user_id + '的数据。', is_temp=True)


# update Channel name
@bot.command(name='rename')
async def rename(msg: Message, *args):
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    name = ' '.join(args)
    logging.info('rename channel id {:} as {:}'.format(msg.ctx.channel.id, name))
    try:
        prefix = extract_ticket_prefix(msg.ctx.channel.name)
        await msg.ctx.channel.update(name=f"{prefix} {name}")
        await msg.reply('重命名成功=w=。', is_temp=True)
    except Exception as e:
        await msg.reply(str(e), is_temp=True)
        await msg.reply('出错啦，请检查错误信息=w=', is_temp=True)


@bot.command(name="assign", aliases=['as'])
async def assign(msg: Message):
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    val = await ticket_controller.assign_user(msg)
    await msg.reply(f"操作成功, 当前数据为：{val}")


@bot.command(name="deassign", aliases=['ds'])
async def design(msg: Message):
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    val = await ticket_controller.design_user(msg)
    await msg.reply(f"操作成功, 当前数据为：{val}")


@bot.command(name="getKey", aliases=["get"])
async def get_user_key(msg: Message, key, user=None):
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    if user is None:
        value = await user_service.try_get_user_key(message=msg, key=key)
    else:
        value = await user_service.try_get_user_key(user_id=user, guild_id=msg.ctx.guild.id, key=key)
    await msg.reply(f"查询到数据：{value}")


@bot.command(name='dice', aliases=['d'])
async def dice(msg: Message, mx: int):
    res = random.randint(1, mx)
    await msg.reply("骰子结果是：{:}".format(res))
    logging.info(str(msg.author.nickname) + '投了个骰子，结果是:' + str(res))


#############################################################################################
# 事件处理模块
# #########################################################################################

# 按钮消息处理
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def onclick(b: Bot, event: Event):
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
        # 后续参数代表对应角色
        await ticket_controller.create_ticket(b, event, args[2:])
        return

    # 关闭Ticket时对第一次按钮点击做询问,此时称作预关闭
    # preCloseTicket_{channelId}_{userId}
    elif event.body['value'].startswith('preCloseTicket_'):
        args = event.body['value'].split('_')
        await ticket_controller.pre_close_ticket(b, event, args[1], args[2])
        return

    # 处理关闭ticket的事件, 关闭的信息开头为closeTicket_
    # closeTicket_{channelId}_{userId}
    elif event.body['value'].startswith('closeTicket_'):
        args = event.body['value'].split('_')
        await ticket_controller.close_ticket(b, event, args[1], args[2])
        return

    # 查询消息发送的服务器
    guild = await b.client.fetch_guild(event.body['guild_id'])
    # 下列为高权限操作
    user_authority = await getUserGuildAuthority(event.body['user_id'], guild)

    # 删除Ticket
    # deleteTicket_{channelId}_{userId}
    if event.body['value'].startswith('deleteTicket_'):

        # 记录日志并鉴权
        logging.info('delete ticket invoked')
        if not await check_auth(user_authority, AUTH.STAFF):
            return

        # 拉取目标频道，发送提示信息，然后删除
        cnl = await b.client.fetch_public_channel(event.body['target_id'])
        await cnl.send('Ticket已经删除，可能需要一段时间同步到您的设备。请不要重复删除')
        args = event.body['value'].split('_')
        await ticket_controller.delete_ticket(b, event, args[1])

    # 重开Ticket
    elif event.body['value'].startswith('reopenTicket_'):
        logging.info('reopen ticket invoked')
        if not await check_auth(user_authority, AUTH.STAFF):
            return
        args = event.body['value'].split('_')
        await ticket_controller.reopen_ticket(b, event, args[1], args[2])

    # 设置角色
    # setRole_{roleName}_{roleId}
    if event.body['value'].startswith('setRole_'):
        if not await check_auth(user_authority, AUTH.ADMIN):
            return
        args = event.body['value'].split('_')
        await ticket_controller.set_role(b, event, args[1], args[2])

    # 设置角色
    # removeRole_{roleName}_{roleId}
    if event.body['value'].startswith('delRole_'):
        if not await check_auth(user_authority, AUTH.ADMIN):
            return
        args = event.body['value'].split('_')
        await ticket_controller.remove_role(b, event, args[1], args[2])
    return


# #########################################################################################
# 定时任务
# #########################################################################################
@bot.task.add_interval(minutes=1)
async def check():
    await check_all(bot)


# #########################################################################################
# 测试指令
# #########################################################################################
@bot.command(name='hello')
async def world(msg: Message):
    await msg.reply("world")


# #########################################################################################
# 主程序入口
# #########################################################################################
if __name__ == "__main__":
    logging.basicConfig(level='INFO', format='[%(asctime)s] [%(levelname)s]: %(message)s (%(filename)s:%(lineno)d)')
    bot.run()

# await channel.update_permission(user, allow=(2048 | 4096))
