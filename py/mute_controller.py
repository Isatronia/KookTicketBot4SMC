# -*- encoding: utf-8 -*-
'''
@File    :   mute_controller.py    
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/17 10:25   ishgrina   1.0         None
'''

# import lib
from . import mute_service
from . import user_service
from . import guild_service
from khl import Bot, Message, Guild, User, Channel, Role

async def mute_user(bot: Bot, user_id: str, guild_id: str, mute_time: int, reason: str):
    # 为用户设置禁言角色并且私聊发送原因
    guild = bot.fetch_guild(guild_id)
