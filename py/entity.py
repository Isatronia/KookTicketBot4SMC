# -*- encoding: utf-8 -*-
'''
@File    :   entity.py
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2024/5/6 19:37   ishgrina   1.0         Entitys using in project
'''



# ###############################################################
# imports
# ###############################################################
from typing import Union
from khl import User, Guild

# ###############################################################
# 项目中用到的实体
# ###############################################################

class Ticket:

    def __init__(self):
        # 票的id
        self.ticketId = None
        # 申请人(id 或 User)
        self.applier = None
        # 票的状态(开启， 关闭， 删除)
        self.status = None
        # 频道的id
        self.channal = None



