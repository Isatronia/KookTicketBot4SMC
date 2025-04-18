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

# import bot
import khl.requester
import khl.api
from khl import Bot, Message, MessageTypes, User, Guild, Event, ChannelTypes
from khl.card import CardMessage, Card, Module, Element, Types
from khl.guild import ChannelCategory

from typing import Union

from .user_service import user_service
from .guild_service import guild_service
from .value import PATH
from .parser import get_time


# #############################################################################
# 拆分部分
#
# bot.py过于冗长，拆分方法到这个文件
# #############################################################################

log = logging.getLogger(__name__)

# 显示通用帮助手册
async def gen_basic_manual(user: User):
    cm = CardMessage()
    cd = Card()
    cd.append(Module.Header('帮助手册'))
    cont = ""
    # 从特定文件读取
    with open(PATH.MAN_DATA, 'r', encoding='utf-8') as f:
        for line in f:
            cont = cont + line
    cd.append(Module.Section(Element.Text(content=cont, type=Types.Text.KMD)))
    cm.append(cd)
    return cm


# 显示自定义手册
async def manual(msg: Message, txt: str):
    if txt == '':
        await msg.reply(await gen_basic_manual(msg.author), is_temp=True)
    else:
        try:
            with open(PATH.MAN_PATH + txt + '.man') as f:
                cm = CardMessage()
                cd = Card()
                cd.append(Module.Header('帮助手册'))
                cont = ""
                for line in f:
                    cont = cont + line
                cd.append(Module.Section(Element.Text(content=cont, type=Types.Text.KMD)))
                cm.append(cd)
                await msg.ctx.channel.send(cm)
        except FileNotFoundError as e:
            await msg.reply("文件不存在，请检查拼写或联系管理员。", )
            return
    return


# 设置角色
async def set_role(b: Bot, event: Event, tag: str, role: str):
    log.info('setting role...')
    # await guild_service.record_if_not_exist(event.body['guild_id'])

    # 获取频道id
    cnl = await b.client.fetch_public_channel(event.body['target_id'])
    g = await b.client.fetch_guild(event.body['guild_id'])
    roles = await g.fetch_roles()
    for r in roles:
        if r.id == int(role):
            action_res = await guild_service.try_set_role_tag(event.body['guild_id'], tag, role)
            if action_res is not None:
                await cnl.send("已成功设置 " + r.name + ' 为 ' + tag + " 角色")
                return
            else:
                await cnl.send("请勿重复添加角色tag", temp_target_id=event.body['user_id'])
                return
    await cnl.send("没有找到 " + role + " 角色, 请尝试重新拉取角色列表")


async def remove_role(b: Bot, event: Event, tag: str, role: str):
    log.info('removing role tag...')

    # 获取频道id和服务器id
    cnl = await b.client.fetch_public_channel(event.body['target_id'])
    g = await b.client.fetch_guild(event.body['guild_id'])
    roles = await g.fetch_roles()
    for r in roles:
        if r.id == int(role):
            action_res = await guild_service.try_remove_role_tag(event.body['guild_id'], tag, role)
            if action_res is not None:
                # 编码卡片消息
                cm = CardMessage(Card(Module.Section(Element.Text(f"已成功移除 {r.name} 的 {tag} 角色"))))
                await cnl.send(cm)
            else:
                await cnl.send(f"操作完成,{r.name}未拥有此tag。", temp_target_id=event.body['user_id'])
            return
    await cnl.send("没有找到 " + role + " 角色, 请尝试重新拉取角色列表")


# 生成新的服务单申请按钮
# 数据格式为 create_ticket_{roleId}
async def setup_ticket_generator(b: Bot, msg: Message, role_name: str):
    # 实现方法 | 发送一个带有按钮的卡片消息，点击该按钮的时候就为机器人发送create_ticket_{roleName}消息
    cnl = msg.ctx.channel

    # 开始构建卡片信息
    card = Card(Module.Section(
        Element.Text(
            f"点击按钮申请一张{role_name}能看到的Ticket\n",
        ),
    ))

    temp_ag = Module.ActionGroup(
        Element.Button("点我开票",
                       value=f"create_ticket_{role_name}",
                       click=Types.Click.RETURN_VAL,
                       theme=Types.Theme.PRIMARY)
    )

    card.append(temp_ag)
    if isinstance(cnl, khl.PublicTextChannel):
        msg_id = await b.client.send(cnl, CardMessage(card))
    else:
        pass
    return


async def assign_user(msg: Message):
    assigned = await user_service.try_get_user_key(msg.author.id, msg.ctx.guild.id, "assign")
    if assigned is None:
        assigned = 1
    else:
        assigned += 1
    await user_service.try_set_user_key(msg.author.id, msg.ctx.guild.id, "assign", assigned)
    log.info(f"assign user {msg.author.nickname}(id:{msg.author.id}) task cnt: {assigned}")
    return assigned


async def design_user(msg: Message):
    assigned = await user_service.try_get_user_key(msg.author.id, msg.ctx.guild.id, "assign")
    if assigned is None:
        assigned = 0
    else:
        assigned = max(assigned - 1, 0)
    await user_service.try_set_user_key(msg.author.id, msg.ctx.guild.id, "assign", assigned)
    log.info(f"design user {msg.author.nickname}(id:{msg.author.id}) task cnt: {assigned}")
    return assigned


# #############################################################################
# Ticket 相关代码
#
# 主要是Ticket生命周期相关代码
# 包括了开启，关闭，重开，删除，预关闭等功能
# #############################################################################

# 创建Ticekt
async def create_ticket(b: Bot, event: Event, ticket_role: Union[list, None] = None) -> Union[str, None]:
    if ticket_role is None:
        ticket_role = list()

    # 如果传进来的是字符串类型的新消息，把它存起来，创建ticket的时候发送提示消息。
    raw_ticket_role = ticket_role[0] if len(ticket_role) == 1 and isinstance(ticket_role[0], str) else None

    # 生成Ticket
    async def gen_ticket(guild: Guild, cate: ChannelCategory):

        sender = int(event.body['user_id'])
        # 查询当前用户已经创建的Ticket数量
        ticket_cnt = await guild_service.apply_ticket(guild.id, event.body['user_id'])

        log.info(f"User {sender} is applying ticket at [{guild.name}] | ticket count:" + str(ticket_cnt))

        # 如果开太多票会被禁止开票
        if ticket_cnt is None:
            cnl = await b.client.fetch_public_channel(event.body['target_id'])
            await cnl.send("您已经发送了过多Ticket,请等待关闭后继续发送", temp_target_id=event.body['user_id'])
            return None

        # 取得服务器全部角色， 用于筛选 @全体成员 和 目标角色
        roles = await guild.fetch_roles()

        # 创建一个新频道, 要用try来防止到达上限造成的bug
        try:
            channal_name = f"ticket {str(ticket_cnt)}"
            if raw_ticket_role is not None:
                channal_name = channal_name + f" [{raw_ticket_role}]"
            cnl = await cate.create_text_channel(channal_name)

        # 开票到频道上限报错
        except khl.requester.HTTPRequester.APIRequestFailed as e:
            # 发送错误提示
            cnl = await b.client.fetch_public_channel(event.body['target_id'])
            await cnl.send(
                "Ticket数量已达Kook支持的上限，请等待先前发放的Ticket关闭后继续申请。\n我们为对您造成的不便深表歉意。",
                temp_target_id=event.body['user_id'])

            # 记得把申请额度还回去，否则会造成虚空开票的数据错误
            await user_service.close(event.body['user_id'], guild.id)
            log.error(e)
            return None

        # 设置其他角色的权限
        for role in roles:
            # 全体成员的权限，禁止看到和说话
            if role.id == 0:
                await cnl.update_role_permission(role, deny=(2048 | 4096))
                break

        # 目标角色的权限，允许其看到这张ticket
        for role in ticket_role:
            await cnl.update_role_permission(role, allow=(2048 | 4096))

        # 该用户的权限设置
        await cnl.update_user_permission(sender, allow=(2048 | 4096))

        # 发送默认消息
        # 默认消息是每次创建完成后默认发送的
        await cnl.send(CardMessage(Card(
            Module.Header('Ticket ' + str(ticket_cnt)),
            Module.Section('Ticket 已经成功创建，请在本频道内发送您的问题，我们会尽快给您回复。'),
            Module.Section('要关闭Ticket, 请点击下方按钮：'),
            Module.ActionGroup(
                Element.Button('关闭Ticket', 'preCloseTicket_' + str(cnl.id) + '_' + str(sender),
                               Types.Click.RETURN_VAL)
            )
        )))
        with open('cfg/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        await cnl.send("(met)here(met)", type=MessageTypes.KMD)
        await cnl.send(
            f'(met){sender}(met) 你的ticket已经建好啦！\n请直接在这里提出你的问题，我们的员工看到后会给您解答。',
            type=MessageTypes.KMD)

        # 没看明白先注释掉，应该是@对应用户组，现在是群发，先不加了
        # await cnl.send('(rol)' + str(target_role_id) + '(rol)', type=MessageTypes.KMD)

        # config中填写"new_ticket"字段可以自动发送其中的消息
        try:
            if 'new_ticket' in guild_service[guild.id] and guild_service[guild.id]['new_ticket'] != "":
                await cnl.send(guild_service[guild.id]['new_ticket'], type=MessageTypes.KMD)
            else:
                pass
        except KeyError as e:
            pass
        except Exception as e:
            pass
        log.info('ticket created.')
        return cnl.id
        # End genTicket

    log.info(get_time() + 'creating ticket for roles: ' + str(ticket_role))

    # 获取对应服务器
    guild = await b.client.fetch_guild(event.body['guild_id'])

    # 数据预处理,获取能看到ticket的角色id。
    # 旧版消息中ticket_role是角色id数组，新版消息中是角色tag。
    try:
        if ticket_role is not None:
            ticket_role = list(map(int, ticket_role))
    except ValueError:
        log.warning(f"Role id maybe not integer(Param is :{ticket_role}) getting role by tag...")
        ticket_role = await guild_service.get_role_by_tag(guild.id, ticket_role[0])

    # 自动更新对应服务器的数据
    try:
        await guild_service.check_guild(guild.id)
        # target_role_id = await guild_service.get_role(guild.id, ticket_role)
    except Exception as e:
        log.warning(e)

    log.info('TicketBot: creating ticket at guild ' + guild.name)

    # 取得全部分类，筛选出Ticket分类
    cate = await guild.fetch_channel_category_list()
    for c in cate:
        if c.name == 'ticket':
            res = await gen_ticket(guild, c)
            if res is not None:
                cnl = await b.client.fetch_public_channel(event.body['target_id'])
                await cnl.send("您的Ticket已经创建，请查看(chn)" + res + "(chn)",
                               type=MessageTypes.KMD,
                               temp_target_id=event.body['user_id'])
            return

    # 没有Ticket分类就不发了，并且报个临时错误
    # TODO: 已经允许了，这是技术欠债(目前先不补，反正没人用)
    # 获取发送频道
    cnl = await b.client.fetch_public_channel(event.body['target_id'])
    await cnl.send("Ticket创建失败，请查看是否存在ticket分类。 *Kook目前不允许机器人创建分类，请手动进行*",
                   type=MessageTypes.KMD,
                   temp_target_id=event.body['user_id'])
    return


# 关闭确认（预关闭）
async def pre_close_ticket(b: Bot, event: Event, channel: str, user: str):
    log.info('pre close ticket...')
    cnl = await b.client.fetch_public_channel(channel)
    await cnl.send(CardMessage(Card(
        Module.Header('Ticket 即将被关闭'),
        Module.Section('请确认是否关闭Ticket？'),
        Module.ActionGroup(
            Element.Button('关闭Ticket', 'closeTicket_' + str(cnl.id) + '_' + str(user), Types.Click.RETURN_VAL)
        )
    )), temp_target_id=str(event.body['user_id']))
    return


# 关闭
async def close_ticket(b: Bot, event: Event, channel: str, user: str):
    log.info('closing ticket...')
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


# 重开
async def reopen_ticket(b: Bot, event: Event, channel: str, user: str):
    log.info('reopening ticket...')
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


# 删除
async def delete_ticket(b: Bot, event: Event, channel: str):
    log.info('deleting ticket...')
    cnl = await b.client.fetch_public_channel(channel)
    guild = await b.client.fetch_guild(event.body['guild_id'])
    await guild.delete_channel(cnl)
    return
