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
import time


class AUTH:
    STAFF = 1
    ADMIN = 2147483648


class PATH:
    GUILD_DATA = './cfg/data.json'
    USER_DATA = './cfg/user.json'
    MUTE_DATA = './cfg/mute.json'
    MAN_DATA = './cfg/usr_man.txt'
    MAN_PATH = './cfg/man/'


class ROLE:
    MUTE = 'mute'
    STAFF = 'staff'


def get_time() -> str:
    sz = time.strftime('%Y-%m-%d %H:%M:%S')
    return '[' + sz + '] : '
