# chat/routing.py
from django.urls import re_path

import prototype.consumers
import chat.consumers

# websocket_urlpatterns = [
#     re_path(r'ws/chat/(?P<chat_id>\d+)/(?P<token>[a-zA-Z0-9._-]+)/$', chat.consumers.ChatConsumer.as_asgi()),
#     re_path(r'ws/chat/(?P<token>[a-zA-Z0-9._-]+)/$', chat.consumers.ChatConsumer.as_asgi()),
#     re_path(r'ws/chat/count/(?P<token>[a-zA-Z0-9._-]+)/$', chat.consumers.CountConsumer.as_asgi()),
#     re_path(r'ws/prototype/(?P<prototype_id>\w+)/$', prototype.consumers.PrototypeConsumer.as_asgi()),
# ]

websocket_urlpatterns = [
    re_path(r'ws/(?P<type>[A-Z]+)/(?P<chat_id>\d+)/(?P<token>[a-zA-Z0-9._-]+)/$', chat.consumers.NewConsumer.as_asgi()),       # for chat messages, type is 'CHAT'
    re_path(r'ws/(?P<type>[A-Z]+)/(?P<token>[a-zA-Z0-9._-]+)/$', chat.consumers.NewConsumer.as_asgi()),                        # for inner message center, type is 'INNER'
    re_path(r'ws/(?P<type>[A-Z]+)/(?P<token>[a-zA-Z0-9._-]+)/$', chat.consumers.NewConsumer.as_asgi()),                        # for count message center, type is 'COUNT'
    re_path(r'ws/prototype/(?P<prototype_id>\w+)/$', prototype.consumers.PrototypeConsumer.as_asgi()),
]
