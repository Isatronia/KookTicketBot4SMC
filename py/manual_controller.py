# -*- encoding: utf-8 -*-
'''
@File    :   manual_controller.py
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2023/2/6 16:04   ishgrina   1.0         None
'''
import logging

# import lib
from khl import Bot, Message, MessageTypes, User, Guild, Event, ChannelTypes
from khl.card import CardMessage, Card, Module, Element, Types
from khl.guild import ChannelCategory

from .value import PATH


async def gen_basic_manual(user: User):
    cm = CardMessage()
    cd = Card()
    cd.append(Module.Header('帮助手册'))

    cont = ""
    with open(PATH.MAN_DATA, 'r', encoding='utf-8') as f:
        for line in f:
            if line == '':
                continue
            cont = cont + "\n" + line

    cd.append(Module.Section(Element.Text(content=cont, type=Types.Text.KMD)))
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
            logging.warning(f"Trying open manual file {txt} but not found.")
            return
    return
