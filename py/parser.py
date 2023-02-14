# -*- encoding: utf-8 -*-
'''
@File    :   parser.py    
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA

@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2023/2/4 13:28   ishgrina   1.0         None
'''

# import lib

import asyncio
import re
import time


async def timeParser(time: str) -> int:
    res = 0

    # RE pattens
    d = re.compile('([0-9]+)d')
    h = re.compile('([0-9]+)h')
    m = re.compile('([0-9]+)m')
    s = re.compile('([0-9]+)s')

    days = d.search(time)
    hours = h.search(time)
    minutes = m.search(time)
    seconds = s.search(time)

    if days:
        res += int(days.group(1)) * 86400
    if hours:
        res += int(hours.group(1)) * 3600
    if minutes:
        res += int(minutes.group(1)) * 60
    if seconds:
        res += int(seconds.group(1))

    return res


async def sec2str(seconds: int) -> str:
    minutes, sec = divmod(seconds, 60)
    hour, minutes = divmod(minutes, 60)
    return '{:}小时{:}分'.format(hour, minutes)


def get_time() -> str:
    sz = time.strftime('%Y-%m-%d %H:%M:%S')
    return '[' + sz + '] : '