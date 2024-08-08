#  Copyright (c) 2024.
#

'''
@File    :   cdk_service.py
@Author  :   Ishgrina
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA
@Version :   1.0
@Modify  :   8/8/2024
@Desciption
--------------------------------------

--------------------------------------
'''
import uuid
from typing import Union

from .value import PATH
from .parser import extract_cdk_command

import json
import logging
from khl import User, Guild
from asyncio import Lock


class CdkServiceImpl:
    _data: dict = {}
    _flock: Lock = Lock()

    def __init__(self):
        self._load()
        pass

    def _get_data(self):
        return CdkServiceImpl._data

    def _load(self):
        try:
            with open(PATH.CDK_PATH, 'r', encoding='utf-8') as f:
                CdkServiceImpl._data = json.load(f)
                pass
        except FileNotFoundError:
            logging.error(
                "Guild data file is not existed. Please check if it's not the first time running this program.")
            CdkServiceImpl._data = {}

    def _store(self):
        with open(PATH.CDK_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._get_data(), f, ensure_ascii=False, indent=4)

    async def check_cdk(self, cdk: str) -> bool:
        if cdk in CdkServiceImpl._data:
            return True
        else:
            return False

    async def generate_cdk(self, cmd: str) -> Union[str, None]:
        command = extract_cdk_command(cmd)
        if command is None:
            return None
        else:
            cdk = str(uuid.uuid4())
            while cdk in self._get_data():
                cdk = str(uuid.uuid4())
            self._get_data()[cdk] = {"command": cmd, "activated": None}
            return cdk

    async def activate_cdk(self, cdk, user: User) -> bool:
        async with CdkServiceImpl._flock:
            if cdk not in self._get_data() or self._get_data()[cdk]["activated"] is not None:
                return False
            command = extract_cdk_command(self._get_data()[cdk]['command'])
            if command.startswith("grant")

cdk_service = CdkServiceImpl()
