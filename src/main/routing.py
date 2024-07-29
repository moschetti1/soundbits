from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path("ws/cheers/<str:user_id>/", consumers.CheerEventConsumer.as_asgi())
]