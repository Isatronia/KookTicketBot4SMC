# -*- encoding: utf-8 -*-
'''
@File    :   ticket_controller.py
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/10 23:03   ishgrina   1.0         None
'''

# import lib
import json
import logging

import khl.requester
from khl import Bot, Message, MessageTypes, User, Guild, Event, ChannelTypes
from khl.card import CardMessage, Card, Module, Element, Types
from khl.guild import ChannelCategory

from typing import Union

from .user_service import user_service
from .guild_service import guild_service
from .value import PATH
from parser import get_time


async def gen_basic_manual(user: User):
    cm = CardMessage()
    cd = Card()
    cd.append(Module.Header('帮助手册'))

    with open(PATH.MAN_DATA, 'r', encoding='utf-8') as f:
        for line in f:
            cd.append(Module.Section(Element.Text(content=line, type=Types.Text.KMD)))

    cm.append(cd)
    return cm


async def manual(msg: Message, txt: str):
    if txt == '':
        await msg.reply(await gen_basic_manual(msg.author), is_temp=True)
    else:
        try:
            with open(PATH.MAN_PATH + txt + '.man') as f:
                cm = CardMessage()
                cd = Card()
                cd.append(Module.Header('帮助手册'))
                for line in f:
                    cd.append(Module.Section(Element.Text(content=line, type=Types.Text.KMD)))
                cm.append(cd)
                await msg.ctx.channel.send(cm)
        except FileNotFoundError as e:
            return
    return


async def set_role(b: Bot, event: Event, tag: str, role: str):
    logging.info('setting role...')
    await guild_service.record_if_not_exist(event.body['guild_id'])
    cnl = await b.client.fetch_public_channel(event.body['target_id'])
    g = await b.client.fetch_guild(event.body['guild_id'])
    roles = await g.fetch_roles()
    for r in roles:
        if r.id == int(role):
            await guild_service.set_role(event.body['guild_id'], tag, role)
            await cnl.send("已成功设置 " + r.name + ' 为 ' + tag + " 角色")
            return
    await cnl.send("没有找到 " + role + " 角色, 请尝试重新拉取角色列表")


# #############################################################################
# Ticket 相关代码
# #############################################################################

# 创建Ticekt
async def create_ticket(b: Bot, event: Event, ticket_role='staff') -> Union[str, None]:
    logging.info(get_time() + 'creating ticket for role: ' + ticket_role)

    # 获取对应服务器
    guild = await b.client.fetch_guild(event.body['guild_id'])

    try:
        await guild_service.record_if_not_exist(guild.id)
        target_role_id = await guild_service.get_role(guild.id, ticket_role)
        if target_role_id is not None:
            target_role_id = int(target_role_id)
    except Exception as e:
        logging.info(e)

    # 生成Ticket
    async def gen_ticket(guild: Guild, cate: ChannelCategory):

        sender = await guild.fetch_user(event.body['user_id'])
        # 查询当前用户已经创建的Ticket数量
        ticket_cnt = await guild_service.apply(guild.id, event.body['user_id'])
        logging.info('ticket count: ' + str(ticket_cnt))
        # 如果开太多票会被禁止开票
        if ticket_cnt is None:
            cnl = await b.client.fetch_public_channel(event.body['target_id'])
            await cnl.send("您已经发送了过多Ticket,请等待关闭后继续发送", temp_target_id=event.body['user_id'])
            return None
        # 取得服务器全部角色， 用于筛选 @全体成员 和 目标角色
        roles = await guild.fetch_roles()
        # 创建一个新频道, 要用try来防止到达上限造成的bug
        try:
            cnl = await cate.create_channel('ticket_' + str(ticket_cnt) + ' for ' + ticket_role, type=ChannelTypes.TEXT)
        except khl.requester.HTTPRequester.APIRequestFailed as e:
            cnl = await b.client.fetch_public_channel(event.body['target_id'])
            await cnl.send("Ticket数量已达Kook支持的上限，请等待原先Ticket关闭后继续申请。\n我们为对您造成的不便深表歉意。",
                           temp_target_id=event.body['user_id'])
            await user_service.close(event.body['user_id'], guild.id)
            logging.error(e)
            return None
        for role in roles:
            if role.id == 0:
                await cnl.update_role_permission(role, deny=(2048 | 4096))
            elif role.id == target_role_id:
                await cnl.update_role_permission(role, allow=(2048 | 4096))
        # 权限设置
        await cnl.update_user_permission(sender, allow=(2048 | 4096))
        # 发送默认消息
        await cnl.send(CardMessage(Card(
            Module.Header('Ticket ' + str(ticket_cnt)),
            Module.Section('Ticket 已经成功创建，请在本频道内发送您的问题，我们会尽快给您回复。'),
            Module.Section('要关闭Ticket, 请点击下方按钮：'),
            Module.ActionGroup(
                Element.Button('关闭Ticket', 'preCloseTicket_' + str(cnl.id) + '_' + str(sender.id),
                               Types.Click.RETURN_VAL)
            )
        )))
        with open('cfg/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        await cnl.send('(met)' + sender.id + '(met) 你的ticket已经建好啦！\n请直接在这里提出你的问题，我们的员工看到后会给您解答。', type=MessageTypes.KMD)
        await cnl.send('(rol)' + str(target_role_id) + '(rol)', type=MessageTypes.KMD)
        try:
            if config['new_ticket'] is not None and config['new_ticket'] != "":
                await cnl.send(config['new_ticket'], type=MessageTypes.KMD)
            else:
                pass
        except KeyError as e:
            pass
        except Exception as e:
            pass
        logging.info('ticket created.')
        return cnl.id



    logging.info('TicketBot: creating ticket at guild ' + guild.name)
    # 取得全部分类，筛选出Ticket分类
    cate = await guild.fetch_channel_category_list()
    for c in cate:
        if c.name == 'ticket':
            res = await gen_ticket(guild, c)
            if res is not None:
                cnl = await b.client.fetch_public_channel(event.body['target_id'])
                await cnl.send("您的Ticket已经创建，请查看(chn)" + res + "(chn)", type=MessageTypes.KMD,
                               temp_target_id=event.body['user_id'])
            return
    # 没有Ticket分类就不发了，并且报个临时错误
    # 获取发送频道
    cnl = await b.client.fetch_public_channel(event.body['target_id'])
    await cnl.send("Ticket创建失败，请查看是否存在ticket分类。 *Kook目前不允许机器人创建分类，请手动进行*", type=MessageTypes.KMD,
                   temp_target_id=event.body['user_id'])
    # await guild.create_channel(name='ticket', type=ChannelTypes.CATEGORY)
    # await create_ticket(b, event)
    # await gen_ticket(channal)
    return


async def pre_close_ticket(b: Bot, event: Event, channel: str, user: str):
    logging.info('pre close ticket...')
    cnl = await b.client.fetch_public_channel(channel)
    await cnl.send(CardMessage(Card(
        Module.Header('Ticket 即将被关闭'),
        Module.Section('请确认是否关闭Ticket？'),
        Module.ActionGroup(
            Element.Button('关闭Ticket', 'closeTicket_' + str(cnl.id) + '_' + str(user), Types.Click.RETURN_VAL)
        )
    )), temp_target_id=str(event.body['user_id']))
    return


async def close_ticket(b: Bot, event: Event, channel: str, user: str):
    logging.info('closing ticket...')
    cnl = await b.client.fetch_public_channel(channel)
    # guild = b.client.fetch_guild(event.body['guild_id'])

    await cnl.update_user_permission(await b.client.fetch_user(user), deny=(2048 | 4096))
    await user_service.close(user, event.body['guild_id'])
    await cnl.send(CardMessage(Card(
        Module.Header('Ticket 已被 ' + event.body['user_info']['nickname'] + ' 关闭'),
        Module.ActionGroup(
            Element.Button('Reopen', 'reopenTicket_' + str(cnl.id) + '_' + str(user), Types.Click.RETURN_VAL),
            Element.Button('Delete', 'deleteTicket_' + str(cnl.id) + '_' + str(user), Types.Click.RETURN_VAL)
        )
    )))
    return


async def reopen_ticket(b: Bot, event: Event, channel: str, user: str):
    logging.info('reopening ticket...')
    cnl = await b.client.fetch_public_channel(channel)

    await cnl.update_user_permission(await b.client.fetch_user(user), allow=(2048 | 4096))
    await user_service.open(user, event.extra['body']['guild_id'])
    await cnl.send(CardMessage(Card(
        Module.Header('Ticket 已重新开启'),
        Module.ActionGroup(
            Element.Button('关闭Ticket', 'preCloseTicket_' + str(cnl.id) + '_' + str(user), Types.Click.RETURN_VAL)
        )
    )))
    return


async def delete_ticket(b: Bot, event: Event, channel: str, user: str):
    logging.info('deleting ticket...')
    cnl = await b.client.fetch_public_channel(channel)
    guild = await b.client.fetch_guild(event.body['guild_id'])
    await guild.delete_channel(cnl)
    return
