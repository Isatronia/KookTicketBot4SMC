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

from guild_service import guild_service
from .cdkserviceimpl import cdk_service
from value import PATH
from khl import Message

async def generate_cdk(msg: Message, command: str):

    await cdk_service.generate_cdk(command)
