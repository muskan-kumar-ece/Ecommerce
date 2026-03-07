from django.urls import path

from .consumers import OrderConsumer

websocket_urlpatterns = [
    path("ws/orders/<int:order_id>/", OrderConsumer.as_asgi()),
]
