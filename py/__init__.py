#  Copyright (c) 2025.
#

'''
@File    :   __init__.py
@Author  :   Ishgrina
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA
@Version :   1.0
@Modify  :   3/29/2025
@Desciption
--------------------------------------

--------------------------------------
'''
from .value import PATH
from pathlib import Path

# Make sure that the directories are exists

for path in PATH.WORK_DIRs:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)

from .guild_service import guild_service
from .mute_service import mute_service
from .user_service import user_service
from .mute_service import mute_service
