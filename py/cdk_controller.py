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

async def generate_cdk(msg: Message, command: str, count: int = 1):
    if count <= 0:
        await msg.reply(f"生成数量有误，请检查指定的数量")
        return
    if count >= 50:
        await msg.reply(f"Kook单条信息存在上限，已将数量指定为50", is_temp=True)
        count = 50
    cdk_list = []
    for i in range(count):
        cdk = await cdk_service.generate_cdk(msg, command)
        cdk_list.append(cdk)
    cdks = "\n".join(cdk_list)
    await msg.reply(f"CDK生成成功, 请保留此Key备用:\n---\n{cdks}", is_temp=True)

async def activate_cdk(msg: Message, cdk: str):
    res = await cdk_service.activate_cdk(cdk, msg)
    if res:
        await msg.reply("CDK使用成功")
    else:
        await msg.reply("出问题了，请检查您输入的内容")