# -*- encoding: utf-8 -*-
'''
@File    :   value.py    
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2022/7/17 9:58   ishgrina   1.0         None
'''
import json
# import lib
import os


# 角色基础权限控制
class AUTH:
    STAFF = 0x00000001
    ADMIN = 0x7fffffff


# 配置文件路径
class PATH:
    BASE_PATH = os.getcwd()
    GUILD_DATA = os.getcwd() + '/cfg/data.json'
    USER_DATA = os.getcwd() + '/cfg/user.json'
    MUTE_DATA = os.getcwd() + '/cfg/mute.json'
    MAN_DATA = os.getcwd() + '/README.md'
    MAN_PATH = os.getcwd() + '/cfg/man/'
    CDK_PATH = os.getcwd() + '/cfg/cdk.json'
    WORK_DIRs = [MAN_PATH, BASE_PATH + '/log/']


# 角色标识
class ROLE:
    MUTE = 'mute'
    STAFF = 'staff'


class __CONFIG:
    def __init__(self):
        self.__dict = {}
        with open(os.getcwd() + '/cfg/config.json', encoding='utf8') as f:
            self.__dict = json.load(f)

    def __getitem__(self, item):
        return self.get_config(item)

    def __setitem__(self, key, value):
        return

    # 配置文件只允许读取字符
    def get_config(self, key: str = None):
        if key is None:
            return None
        if not isinstance(key, str):
            return None
        else:
            try:
                return self.__dict[key]
            except KeyError:
                return None


config = __CONFIG()
