from decimal import Decimal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing.websocket import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from core.asgi import application

from .models import Order
from .realtime import get_order_updates_group_name, handle_order_update_event


@override_settings(
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }
)
class OrderConsumerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="wsbuyer@example.com",
            password="StrongPass123",
            name="WS Buyer",
        )
        self.other_user = get_user_model().objects.create_user(
            email="otherws@example.com",
            password="StrongPass123",
            name="Other WS",
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal("499.00"),
            status=Order.Status.PENDING,
        )

    def test_authenticated_order_owner_can_connect(self):
        communicator = WebsocketCommunicator(application, f"/ws/orders/{self.order.id}/")
        communicator.scope["user"] = self.user

        connected, _ = async_to_sync(communicator.connect)()
        self.assertTrue(connected)

    def test_order_update_event_handler_broadcasts_to_user_group(self):
        self.order.status = Order.Status.SHIPPED
        self.order.save(update_fields=["status", "updated_at"])

        channel_layer = get_channel_layer()
        channel_name = async_to_sync(channel_layer.new_channel)("orders-tests")
        group_name = get_order_updates_group_name(self.user.id)
        async_to_sync(channel_layer.group_add)(group_name, channel_name)

        handle_order_update_event(self.order)
        payload = async_to_sync(channel_layer.receive)(channel_name)

        self.assertEqual(payload["type"], "order.update")
        self.assertEqual(payload["order_id"], self.order.id)
        self.assertEqual(payload["status"], Order.Status.SHIPPED)
        self.assertEqual(payload["status_label"], "Shipped")
        self.assertIn("updated_at", payload)

    def test_order_update_signal_broadcasts_status_changes(self):
        channel_layer = get_channel_layer()
        channel_name = async_to_sync(channel_layer.new_channel)("orders-tests")
        group_name = get_order_updates_group_name(self.user.id)
        async_to_sync(channel_layer.group_add)(group_name, channel_name)

        self.order.status = Order.Status.SHIPPED
        self.order.save(update_fields=["status", "updated_at"])

        payload = async_to_sync(channel_layer.receive)(channel_name)
        self.assertEqual(payload["type"], "order.update")
        self.assertEqual(payload["order_id"], self.order.id)
        self.assertEqual(payload["status"], Order.Status.SHIPPED)
        self.assertEqual(payload["status_label"], "Shipped")

    def test_anonymous_user_connection_is_rejected(self):
        communicator = WebsocketCommunicator(application, f"/ws/orders/{self.order.id}/")

        connected, _ = async_to_sync(communicator.connect)()
        self.assertFalse(connected)

    def test_non_owner_connection_is_rejected(self):
        communicator = WebsocketCommunicator(application, f"/ws/orders/{self.order.id}/")
        communicator.scope["user"] = self.other_user

        connected, _ = async_to_sync(communicator.connect)()
        self.assertFalse(connected)
