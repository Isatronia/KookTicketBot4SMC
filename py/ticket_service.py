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


class TicketService:
    _ticket_update_lock = Lock()
    _ticket_log = {}
    _ticket_channels = set()

    def __init__(self):
        for file_path in glob.glob(os.path.join(PATH.TICKET_DATA_DIRECTORY, "**", "*.json"), recursive=True):
            ticket = Ticket.load_from_file(file_path)
            if ticket:
                if ticket.guild_id not in TicketService._ticket_log:
                    TicketService._ticket_log[ticket.guild_id] = {}
                TicketService._ticket_log[ticket.guild_id][ticket.ticket_id] = ticket
                TicketService._ticket_channels.add(ticket.channel_id)

    def close_ticket(self, guild_id: int, ticket_id: int):
        ticket = TicketService._ticket_log[guild_id][ticket_id]
        ticket.state = TKSTAT.CLOSED

    def open_ticket(self, guild_id: int, ticket_id: int, channel_id: int, applier: int):
        ticket = Ticket(ticket_id=ticket_id, guild_id=guild_id, channel_id=channel_id, applier=applier,
                        state=TKSTAT.OPEN, msg_log=[])
        TicketService._ticket_log[guild_id][ticket_id] = ticket
        TicketService._ticket_channels.add(channel_id)

    def modify_ticket(self, ticket: Ticket = None):
        if ticket is None:
            return
        if ticket.guild_id is None or ticket.ticket_id is None:
            return
        temp: Ticket = TicketService._ticket_log[ticket.guild_id][ticket.ticket_id]
        if temp.channel_id in TicketService._ticket_channels:
            TicketService._ticket_channels.discard(temp.channel_id)
            TicketService._ticket_channels.add(ticket.channel_id)
        temp.update(ticket)

    def on_message(self, message: Message):
        if str(message.ctx.channel) not in TicketService._ticket_channels:
            return
