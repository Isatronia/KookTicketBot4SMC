#  Copyright (c) 2024.
#

'''
@File    :   cdk_controller.py
@Author  :   Ishgrina
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA
@Version :   1.0
@Modify  :   8/8/2024
@Desciption
--------------------------------------

--------------------------------------
'''
from khl import Message

from .guild_service import guild_service
from .cdk_service import cdk_service
from .value import PATH

async def generate_cdk(msg: Message, command: str):
    cdk = await cdk_service.generate_cdk(msg, command)
    await msg.reply(f"CDK生成成功, 请保留此Key备用:\n*{cdk}*", is_temp=True)

async def activate_cdk(msg: Message, cdk: str):
    res = await cdk_service.activate_cdk(cdk, msg)
    if res:
        await msg.reply("CDK使用成功")
    else:
        await msg.reply("出问题了，请检查您输入的内容")