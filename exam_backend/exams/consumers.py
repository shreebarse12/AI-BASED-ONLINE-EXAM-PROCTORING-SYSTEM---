import json
from channels.generic.websocket import AsyncWebsocketConsumer

class WarningConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("warnings", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("warnings", self.channel_name)

    async def send_warning(self, event):
        await self.send(text_data=json.dumps(event))
