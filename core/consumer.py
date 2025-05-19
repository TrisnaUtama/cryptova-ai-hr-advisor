import json
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.chat.tasks import process_chat


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        if self.channel_layer is None:
            print("Channel layer is None")
            return

        await self.channel_layer.group_add("notifications", self.channel_name)

    async def disconnect(self, code):
        if self.channel_layer is None:
            print("Channel layer is None")
            return

        await self.channel_layer.group_discard("notifications", self.channel_name)

    async def send_notification(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.group_name = f"chat_{self.session_id}"
        await self.accept()

        if self.channel_layer is None:
            print("Channel layer is None")
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def disconnect(self, code):
        if self.channel_layer is None:
            print("Channel layer is None")
            return

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        print("Received data:", text_data, flush=True)
        if text_data is not None:
            text_data_json = json.loads(text_data)
            message = text_data_json.get("message")
            user = self.scope["user"]
            if not user.is_authenticated:
                print("User not authenticated, ignoring message.", flush=True)
                return

            user_id = user.id
            process_chat(message, self.session_id, user_id)

    async def send_message(self, event):
        # Support both string and dict message
        msg = event["message"]
        if isinstance(msg, dict):
            await self.send(
                text_data=json.dumps(
                    {"message": msg["message"], "done": msg.get("done", False)}
                )
            )
        else:
            await self.send(text_data=json.dumps({"message": msg, "done": False}))
