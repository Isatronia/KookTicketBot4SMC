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
import asyncio
import threading
from logging.handlers import TimedRotatingFileHandler

# import khl.py
from khl import Bot, Message, Event, EventTypes
from khl.card import CardMessage, Card, Module, Element, Types, Struct

# #############################################################################
# 初始化程序代码
# #############################################################################
# 设置logging
logger = logging.getLogger()
log_handler = TimedRotatingFileHandler(
    filename=os.getcwd() + '/log/bot.log',  # Base filename
    when='midnight',  # Split logs at midnight
    interval=1,  # Interval of 1 day
    backupCount=30  # Keep the last 30 log files
)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s (%(filename)s:%(lineno)d)')
log_handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

log = logging.getLogger(__name__)

# 设置程序的工作路径
os.chdir(os.path.dirname(os.path.abspath(__file__)))
logging.info(f"Current working directory is: {os.getcwd()}")

# import coded scripts.
import py.ticket_controller as ticket_controller
from py.cdk_controller import generate_cdk, activate_cdk
from py.guild_service import guild_service
from py.mute_service import mute_service
from py.mute_controller import mute_user, unmute_user, check_all, mute_suspend
from py.parser import timeParser, get_time, extract_ticket_prefix
from py.user_service import user_service
from py.utils import check_authority, getUserGuildAuthority, has_role
from py.value import AUTH, ROLE, config

# 全局变量定义
# 初始化机器人
bot = Bot(token=config['token'])

# 多线程 --- 线程间通信变量
mute_observer_run = threading.Event()

mute_observer_thread = threading.Thread(
    target=mute_suspend,
    args=(bot, mute_observer_run),
    daemon=True)
bot.mute_thread = mute_observer_thread
bot.event_run_mute = mute_observer_run


@bot.on_startup
async def startup(b: Bot):
    log.info(f"Initializing bot...")
    try:
        b.event_run_mute.set()
        b.mute_thread.start()
        pass
    except KeyError:
        log.warning(f"The bot have not registered mute thread.")


@bot.on_shutdown
async def shutdown(b: Bot):
    b.event_run_mute.clear()
    log.info("Shutting down...")
    await user_service.store()
    log.info("User data saved.")
    await guild_service.store()
    log.info("Guild data saved.")
    await mute_service.store()
    log.info("Mute data saved.")
    log.info("Waiting mute thread join...")
    b.mute_thread.join()


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
    log.info('setting role: ' + rolename + 'at guild ' + msg.ctx.guild.name + ' guild id is: ' + msg.ctx.guild.id)
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
    log.info(f"deleting role: {rolename} at guild {msg.ctx.guild.name} witch id is: {msg.ctx.guild.id}")
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
    log.info('listting role...')
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
    log.info('trying mute: ' + user_id + ' ' + mute_time + ' for ' + reason)

    # 获取用户对象
    user_obj = await bot.client.fetch_user(user_id)

    # 鉴权
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        log.info(get_time() + 'Unauthorized, mute action rejected.')
        return

    # Log
    log.info(
        f"Authorized. Mute process started muting {user_id} in guild {msg.ctx.guild.name}(id:{msg.ctx.guild.id})")

    # 检查静音用户是否存在，并设置静音角色 （Tag）
    mute_role = await guild_service.get_role_by_tag(msg.ctx.guild.id, ROLE.MUTE)

    # 错误检测，没有设置静音角色（Tag）
    if mute_role is None:
        log.warning(get_time() + 'mute role not found. cur data is : + \n' + str(guild_service._data))
        await msg.ctx.channel.send(CardMessage(Card(
            Module.Header('Error occurred'),
            Module.Section('还没有设置Mute角色啊 kora!!')
        )), temp_target_id=msg.author.id)
        return

    try:
        mute_time = await timeParser(mute_time)
        log.info(get_time() + 'mute time resolved: ' + str(mute_time))
        # 实现禁言
        await mute_user(msg, user_obj, mute_time, reason)
    except Exception as e:
        log.info(str(e))
        # await msg.reply(str(e), is_temp=True)
        await msg.reply('出错啦，请联系管理员检查错误信息=w=', is_temp=True)
    log.info(get_time() + f"succeed muted {user_id} {mute_time} for {reason}")


# 取消静音用户（移除静音角色）
@bot.command(name='unmute')
async def unmute(msg: Message, userid: str):
    # 鉴权
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return

    # log
    log.info('unmute user ' + userid + ' at ' + msg.ctx.guild.name + '(id is {:} )'.format(msg.ctx.guild.id))

    # 获取用户
    user = await bot.client.fetch_user(userid)

    try:
        await unmute_user(msg, user)
    except Exception as e:
        log.error(str(e))
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
    log.info('cleaning user data: {:} at {:}(id is: {:})'.format(user_id, msg.ctx.guild.name, msg.ctx.guild.id))
    await user_service.reset(user_id, msg.ctx.guild.id)
    await msg.reply('已清除用户' + user_id + '的数据。', is_temp=True)


# update Channel name
@bot.command(name='rename')
async def rename(msg: Message, *args):
    if not await check_authority(msg, AUTH.STAFF | AUTH.ADMIN):
        return
    new_name = ' '.join(args)
    log.info('rename channel id {:} as {:}'.format(msg.ctx.channel.id, new_name))
    try:
        prefix = extract_ticket_prefix(msg.ctx.channel.name)
        await msg.ctx.channel.update(name=f"{prefix} {new_name}")
        await msg.reply(f'已将频道重命名为 {new_name}')
    except Exception as e:
        await msg.reply(str(e), is_temp=True)
        await msg.reply('出错啦，请联系开发者检查错误信息=w=', is_temp=True)


@bot.command(name="setKey", aliases=['sk', 'config', 'cfg'])
async def force_set_key(msg: Message, *args):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    sz = ' '.join(args)
    cmd_list = [s.strip() for s in sz.split(':')[:2]]
    if await guild_service.set_guild_config(msg.ctx.guild.id, *cmd_list) is not None:
        await msg.reply('操作成功')
    else:
        await msg.reply('操作出错，请联系管理员')


@bot.command(name="listKey", aliases=['showConfig'])
async def list_guild_keys(msg: Message):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    txt = await guild_service.list_guild_config(msg.ctx.guild.id)
    await msg.ctx.channel.send(f'```json\n{txt}```')


@bot.command(name="removeKey", aliases=['rk'])
async def remove_guild_keys(msg: Message, *args):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    if '--all' in args or '--a' in args:
        res = await guild_service.clear_guild_config(msg.ctx.guild.id)
    else:
        res = await guild_service.clear_guild_config_by_key(msg.ctx.guild.id, args[0])
    await msg.reply("操作出错，请联系管理员" if res is None else "操作成功")


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
    log.info(str(msg.author.nickname) + '投了个骰子，结果是:' + str(res))


@bot.command(name='generate', aliases=['cdk'])
async def gen_cdk(msg: Message, *args):
    if not await check_authority(msg, AUTH.ADMIN):
        return
    count = 1
    if args[0] == '-n':
        command = ' '.join(args[2:])
        count = int(args[1])
    else:
        command = ' '.join(args)
    await generate_cdk(msg, command, count=count)
    return


@bot.command(name='activate', aliases=['act'])
async def act_cdk(msg: Message, cdk: str):
    await activate_cdk(msg, cdk)


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

    log.info(get_time() + 'event received... body is:\n' + str(event.body))
    guild_id = event.body['guild_id']
    if event.body['value'].startswith('create_ticket_'):
        # 这是新的需求，开票只能由白名单玩家进行
        whitelistmode = await guild_service.get_guild_config(guild_id, "whitelist")
        if whitelistmode is not None and whitelistmode.lower() in ("true", "on"):
            try:
                authorized_role = await guild_service.get_guild_config(guild_id, "create_ticket_role")
                if authorized_role is None or not await has_role(b=b, event=event, role=authorized_role):
                    channel = await b.client.fetch_public_channel(event.body['target_id'])
                    await channel.send("您没有权限进行此操作", temp_target_id=event.body['user_id'])
                    return
            except KeyError as e:
                log.warning(f"Error occurred applying ticket, please see log file.")

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
        log.info('delete ticket invoked')
        if not await check_auth(user_authority, AUTH.STAFF):
            return

        # 拉取目标频道，发送提示信息，然后删除
        cnl = await b.client.fetch_public_channel(event.body['target_id'])
        await cnl.send('Ticket已经删除，可能需要一段时间同步到您的设备。请不要重复删除')
        args = event.body['value'].split('_')
        await ticket_controller.delete_ticket(b, event, args[1])

    # 重开Ticket
    elif event.body['value'].startswith('reopenTicket_'):
        log.info('reopen ticket invoked')
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
# @bot.task.add_interval(minutes=1)
# async def check():
#     await check_all(bot)


# #########################################################################################
# 测试指令
# #########################################################################################
@bot.command(name='hello', aliases=['ping', 'h'])
async def world(msg: Message):
    roles = await msg.ctx.guild.fetch_roles()
    await msg.reply("Online")


# #########################################################################################
# 主程序入口
# #########################################################################################

bot.run()

# await channel.update_permission(user, allow=(2048 | 4096))
