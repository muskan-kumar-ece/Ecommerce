from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Order
from .realtime import get_order_updates_group_name


class OrderConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        order_id = self.scope["url_route"]["kwargs"]["order_id"]
        has_access = await self._user_has_order_access(user.id, order_id)
        if not has_access:
            await self.close(code=4403)
            return

        self.group_name = get_order_updates_group_name(user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def order_update(self, event):
        if event["order_id"] != self.scope["url_route"]["kwargs"]["order_id"]:
            return
        await self.send_json(
            {
                "order_id": event["order_id"],
                "status": event["status"],
                "status_label": event["status_label"],
                "updated_at": event["updated_at"],
            }
        )

    @database_sync_to_async
    def _user_has_order_access(self, user_id, order_id):
        return Order.objects.filter(id=order_id, user_id=user_id).exists()
