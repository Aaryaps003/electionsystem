from django.urls import path

from .consumers import ResultsConsumer

websocket_urlpatterns = [path("ws/results/", ResultsConsumer.as_asgi())]
