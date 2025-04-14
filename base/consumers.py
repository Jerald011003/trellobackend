import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SignalingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("video_chat", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("video_chat", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send("video_chat", {
            'type': 'signal_message',
            'message': data
        })
    async def signal_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))
