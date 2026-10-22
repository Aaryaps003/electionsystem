from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from . import services


class ResultsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(services.GROUP, self.channel_name)
        await self.accept()
        # Send the current state right away so the page never starts empty.
        await self.send_json(await database_sync_to_async(services.snapshot)())

    async def disconnect(self, code):
        await self.channel_layer.group_discard(services.GROUP, self.channel_name)

    async def results_update(self, event):
        await self.send_json(event["data"])
