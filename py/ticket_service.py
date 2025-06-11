#  Copyright (c) 2025.
#

'''
@File    :   ticket_service.py
@Author  :   Ishgrina
@Contact :   naragnova88@gmail.com
@License :   CC BY-NC-SA
@Version :   1.0
@Modify  :   2/9/2025
@Desciption
--------------------------------------

--------------------------------------
'''
import glob
import os
from asyncio import Lock

from khl import Message

from py.value import PATH
from entity import Ticket, TKSTAT


class TicketChannel:
    def __init__(self, channel: str, guild: str, index: str):
        self.channel_id = channel
        self.guild_id = guild
        self.ticket_index = index

    def __hash__(self):
        return hash(self.channel_id)

    def __eq__(self, other) -> bool:
        if isinstance(other, TicketChannel):
            return self.channel_id == other.channel_id
        return False

    def __repr__(self):
        return f"Ticket Channel({self.channel_id}): [Guild: {self.guild_id}\tIndex: {self.ticket_index}]"

class TicketServiceImpl:
    _ticket_update_lock = Lock()
    _ticket_log = {}
    _ticket_channels = set()

    def __init__(self):
        for file_path in glob.glob(os.path.join(PATH.TICKET_DATA_DIRECTORY, "**", "*.json"), recursive=True):
            ticket = Ticket.load_from_file(file_path)
            if ticket:
                if ticket.guild_id not in TicketServiceImpl._ticket_log:
                    TicketServiceImpl._ticket_log[ticket.guild_id] = {}
                TicketServiceImpl._ticket_log[ticket.guild_id][ticket.ticket_id] = ticket
                TicketServiceImpl._ticket_channels.add(ticket.channel_id)

    async def close_ticket(self, guild_id: str, ticket_id: str):
        async with self._ticket_update_lock:
            if isinstance(TicketServiceImpl._ticket_log[guild_id][ticket_id], Ticket):
                TicketServiceImpl._ticket_log[guild_id][ticket_id].state = TKSTAT.CLOSED

    async def open_ticket(self, guild_id: str, ticket_id: str, channel_id: str, applier: str):
        async with self._ticket_update_lock:
            # Create new ticket.
            ticket = Ticket(ticket_id=ticket_id,
                            guild_id=guild_id,
                            channel_id=channel_id,
                            applier=applier,
                            state=TKSTAT.OPEN,
                            msg_log=[])

            TicketServiceImpl._ticket_log[guild_id][ticket_id] = ticket
            TicketServiceImpl._ticket_channels.add(channel_id)

    async def modify_ticket(self, ticket: Ticket = None):
        if ticket is None:
            return
        if ticket.guild_id is None or ticket.ticket_id is None:
            return
        async with self._ticket_update_lock:
            target_ticket: Ticket = TicketServiceImpl._ticket_log[ticket.guild_id][ticket.ticket_id]
            if target_ticket.channel_id in TicketServiceImpl._ticket_channels:
                TicketServiceImpl._ticket_channels.discard(target_ticket.channel_id)
                TicketServiceImpl._ticket_channels.add(ticket.channel_id)
            target_ticket.update(ticket)

    async def on_message(self, message: Message):
        if str(message.ctx.channel) not in TicketServiceImpl._ticket_channels:
            return
        async with self._ticket_update_lock:
            ticket_info = self._ticket_channels.get(str(message.ctx.channel))
            guild_id, ticket_id = ticket_info.guild_id, ticket_info.ticket_index
            self._ticket_log[guild_id][ticket_id].msg_log.append(message.content)


ticket_service = TicketServiceImpl()
