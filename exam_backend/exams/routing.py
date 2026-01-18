from django.urls import re_path
from .consumers import WarningConsumer

websocket_urlpatterns = [
    re_path(r"ws/warnings/$", WarningConsumer.as_asgi()),
]
