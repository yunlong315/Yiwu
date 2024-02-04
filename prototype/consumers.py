from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from app.tools import *
from app.tools2 import *
from chat.consumers import get_user_by_id
from app.models import *


class PrototypeConsumer(WebsocketConsumer):
    def connect(self):
        # 从url里获取聊天室名字，为每个房间建立一个频道组
        self.prototype_id = self.scope['url_route']['kwargs']['prototype_id']
        self.prototype_group_name = 'prototype_%s' % self.prototype_id

        if ProtoType.objects.filter(prototype_id=self.prototype_id):
            # 将当前频道加入频道组
            async_to_sync(self.channel_layer.group_add)(
                self.prototype_group_name,
                self.channel_name
            )
            self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.prototype_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        change = text_data_json['change']
        token = text_data_json['token']
        prototype_id = text_data_json['prototype_id']
        user = get_user_by_id(parse_token(token)['user_id'])
        prototype = get_prototype_by_id(prototype_id)

        print('---debug info---   [receiving change]   user:' + user.user_nickname + '   ' + 'change:' + change)

        # 保存变更
        new_change = ChangeInPrototype(cip_prototype= prototype, cip_content=change)
        new_change.save()

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'send_change',
                'change': change
            }
        )

    def send_change(self, event):
        change = event['change']
        self.send(text_data=json.dumps({
            'change': f'{change}'
        }))

        print('---debug info---   [broadcasting change above]')


def get_prototype_by_id(prototype_id):
    return ProtoType.objects.get(prototype_id=prototype_id)
