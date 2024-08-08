# -*- encoding: utf-8 -*-
'''
@File    :   value.py    
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/17 9:58   ishgrina   1.0         None
'''

# import lib
import os

# 角色基础权限控制
class AUTH:
    STAFF = 0x00000001
    ADMIN = 0x7fffffff

# 配置文件路径
class PATH:
    GUILD_DATA = os.getcwd() + '/cfg/data.json'
    USER_DATA = os.getcwd() + '/cfg/user.json'
    MUTE_DATA = os.getcwd() + '/cfg/mute.json'
    MAN_DATA = os.getcwd() + '/README.md'
    MAN_PATH = os.getcwd() + '/cfg/man/'
    CDK_PATH = os.getcwd() + '/cfg/cdk.json'

# 角色标识
class ROLE:
    MUTE = 'mute'
    STAFF = 'staff'


