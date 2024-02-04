from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from app import tools2
from app.tools import *
from app.tools2 import *
from channels.layers import get_channel_layer, channel_layers


# class CountConsumer(WebsocketConsumer):
#     token = ''
#
#     def connect(self):
#         self.token = self.scope['url_route']['kwargs']['token']
#         user_id = parse_token(self.token)['user_id']
#         async_to_sync(self.channel_layer.group_add)(
#             'count' + str(user_id),
#             self.channel_name
#         )
#         self.accept()
#
#     def disconnect(self, code):
#         user_id = parse_token(self.token)['user_id']
#         async_to_sync(self.channel_layer.group_discard)(
#             'count' + user_id,
#             self.channel_name
#         )
#
#     def receive(self, text_data=None, bytes_data=None):
#         pass
#
#     def num_message(self, event):
#         print('?????????????????????????????????????????????????')
#         num = event['num']
#         self.send(text_data=json.dumps({
#             'num': f'{num}',
#         }))
#
#
# class ChatConsumer(WebsocketConsumer):
#     chat_id = -1
#     token = ''
#
#     # def __int__(self):
#     #     tools2.SENDER_LAYER = self.channel_layer
#     #     super()
#
#     def connect(self):
#         # for chat
#         # create a channel named chat_id
#         if 'chat_id' in self.scope['url_route']['kwargs'] and 'token' in self.scope['url_route']['kwargs']:
#             print(111)
#             self.chat_id = self.scope['url_route']['kwargs']['chat_id']
#             self.token = self.scope['url_route']['kwargs']['token']
#             if Chat.objects.filter(chat_id=self.chat_id) \
#                     and UserChat.objects.filter(user=User.objects.get(user_id=parse_token(self.token)['user_id']),
#                                                 chat=Chat.objects.get(chat_id=self.chat_id)):
#                 print(333)
#                 print(self.chat_id)
#                 async_to_sync(self.channel_layer.group_add)(
#                     str(self.chat_id),
#                     self.channel_name
#                 )
#                 print('---websocket debug info---   [in connect()]   connected to chat_id:' + self.chat_id)
#                 self.accept()
#             else:
#                 self.disconnect(0)
#
#         # for message center
#         # create a channel named token
#         elif 'token' in self.scope['url_route']['kwargs']:
#             print(222)
#             self.token = self.scope['url_route']['kwargs']['token']
#             user_id = parse_token(self.token)['user_id']
#             encrypted_id = encrypt(user_id)
#             async_to_sync(self.channel_layer.group_add)(
#                 str(user_id),
#                 self.channel_name
#             )
#             print('---websocket debug info---   [in connect()]   connected to token:' + self.token[:20] + '...')
#             self.accept()
#
#         # illegal websocket request
#         else:
#             print('---websocket debug info---   [in connect()]   disconnect while connecting:')
#             self.disconnect(0)
#
#     def disconnect(self, close_code):
#         async_to_sync(self.channel_layer.group_discard)(
#             str(self.chat_id) if self.chat_id != -1 else str(parse_token(self.token)['user_id']),
#             self.channel_name
#         )
#
#     def receive(self, text_data):
#         # require 'message' 'token'
#         text_data_json = json.loads(text_data)
#         message = text_data_json['message']
#         token = text_data_json['token']
#         user_id = parse_token(token)['user_id']
#         message_type = text_data_json['message_type'] if 'message_type' in text_data_json else 'text'
#         user = get_user_by_id(user_id)
#         chat = Chat.objects.get(chat_id=self.chat_id)
#
#         print(
#             '---websocket debug info---   [in receive()]   user:' + user.user_nickname + '   ' + 'chat:' + chat.chat_name + '   ' + 'message:' + message)
#
#         if 'decoy' in text_data_json:
#             decoy_message = Message.objects.get(message_id=text_data_json['decoy'])
#             async_to_sync(self.channel_layer.group_send)(
#                 str(self.chat_id),
#                 {
#                     'type': 'chat_message',
#                     'user_id': '',
#                     'message_id': decoy_message.message_id,
#                     'message': '',
#                     'message_type': '',
#                     'user_nickname': '',
#                     'user_avatar': '',
#                     'time': '',
#                     'forward_type': ''
#                 }
#             )
#         else:
#             # 存储message
#             storage_message = Message(message_description=message, message_from=user, message_to=chat,
#                                       message_type=message_type)
#             storage_message.save()
#
#             # 检查@
#             chat_user_list = get_chat_user(chat)
#             print([x.user_nickname for x in chat_user_list])
#             at_user_list = check_at(message, chat_user_list)
#
#             for single_user in chat_user_list:
#                 # 更新UserChat
#                 if UserChat.objects.filter(user=single_user, chat=chat):
#                     user_chat = UserChat.objects.get(user=single_user, chat=chat)
#                     user_chat.is_read = False
#                     user_chat.save()
#                 else:
#                     user_chat = UserChat(user=single_user, chat=chat, is_read=False)
#                     user_chat.save()
#
#                 # 更新UserMessage
#                 if UserMessage.objects.filter(user=single_user, message=storage_message):
#                     user_message = UserMessage.objects.get(user=single_user, message=storage_message)
#                     user_message.is_read = False
#                     if 'at' in text_data_json and single_user in at_user_list:
#                         user_message.is_at = True
#                     user_message.save()
#                 else:
#                     user_message = UserMessage(user=single_user, message=storage_message, is_read=False)
#                     if 'at' in text_data_json and single_user in at_user_list:
#                         user_message.is_at = True
#                     user_message.save()
#
#                 print(single_user.user_nickname)
#                 print(at_user_list)
#
#                 if single_user in at_user_list:
#                     new_at = At(at_user=single_user, at_from=user, at_type='message', at_message=storage_message)
#                     new_at.save()
#
#                     print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
#                     _channel_layer = channel_layers[CountConsumer.channel_layer_alias]
#                     async_to_sync(_channel_layer.group_send)(
#                         'count' + str(user.user_id),
#                         {
#                             'type': 'num_message',
#                             'num': get_unread_at_num(user)
#                         }
#                     )
#
#                     # 提醒消息中心
#                     data = new_at.info()
#                     data['type'] = 'at_message'
#                     async_to_sync(self.channel_layer.group_send)(
#                         str(single_user.user_id),
#                         data
#                     )
#
#             async_to_sync(self.channel_layer.group_send)(
#                 str(self.chat_id),
#                 {
#                     'type': 'chat_message',
#                     'user_id': user.user_id,
#                     'message_id': storage_message.message_id,
#                     'message': message,
#                     'message_type': message_type,
#                     'user_nickname': user.user_nickname,
#                     'user_avatar': user.user_avatar,
#                     'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
#                     'forward_type': storage_message.forward_type
#                 }
#             )
#
#     def at_message(self, event):
#         message_id = event['message_id']
#         message_from_name = event['message_from_name']
#         message_time = event['message_time']
#         message_content = event['message_content']
#         at_type = event['at_type']
#         if_read = event['if_read']
#
#         # 通过websocket发送消息到客户端
#         self.send(text_data=json.dumps({
#             'message_id': f'{message_id}',
#             'message_from_name': f'{message_from_name}',
#             'message_time': f'{message_time}',
#             'message_content': f'{message_content}',
#             'type': f'{at_type}',
#             'if_read': f'{if_read}',
#         }))
#         print('---websocket debug info---   [in at_message()] broadcasting message to message center')
#
#     def chat_message(self, event):
#         message = event['message']
#         message_id = event['message_id']
#         message_type = event['message_type']
#         user_nickname = event['user_nickname']
#         user_avatar = event['user_avatar']
#         time = event['time']
#         short_time = event['time'][-5:]
#         user_id = event['user_id']
#         forward_type = event['forward_type']
#
#         # 通过websocket发送消息到客户端
#         self.send(text_data=json.dumps({
#             'user_id': f'{user_id}',
#             'chat_content': f'{message}',
#             'message_type': f'{message_type}',
#             'user_name': f'{user_nickname}',
#             'avatar': f'{user_avatar}',
#             'post_time': f'{time}',
#             'post_short_time': f'{short_time}',
#             'message_id': f'{message_id}',
#             'forward_type': f'{forward_type}'
#         }))
#
#         print('---websocket debug info---   [in chat_message()] broadcasting message to chat')


def get_user_by_id(user_id):
    if User.objects.filter(user_id=user_id):
        return User.objects.get(user_id=user_id)


# def get_chat_by_name(name):
#     if Chat.objects.filter(chat_name=name):
#         return Chat.objects.get(chat_name=name)


# def get_history_messages(chat_name):
#     chat = get_chat_by_name(chat_name)
#     history_messages = list(Message.objects.filter(message_to=chat))
#     history_messages = sorted(history_messages, key=lambda x: x.message_time.__str__())
#     return history_messages


def check_at(message, user_list):
    res = []

    if '@所有人 ' in message:
        res = [user_list]
        return res

    for user in user_list:
        check_str = '@' + user.user_nickname + ' '
        if check_str in message:
            res.append(user)
    return res


'''



























'''

TYPE_CHAT = 'CHAT'
TYPE_INNER = 'INNER'
TYPE_COUNT = 'COUNT'


class NewConsumer(WebsocketConsumer):
    type = ''
    token = ''
    chat_id = -1

    def connect(self):
        self.type = self.scope['url_route']['kwargs']['type']

        if self.type == TYPE_CHAT:
            self.chat_id = self.scope['url_route']['kwargs']['chat_id']
            self.token = self.scope['url_route']['kwargs']['token']
            async_to_sync(self.channel_layer.group_add)(
                str(self.chat_id),
                self.channel_name
            )
            print('---websocket debug info---   [in connect() with type CHAT]   connected to chat_id:' + self.chat_id)
            self.accept()

        elif self.type == TYPE_INNER:
            self.token = self.scope['url_route']['kwargs']['token']
            user_id = parse_token(self.token)['user_id']
            async_to_sync(self.channel_layer.group_add)(
                str(user_id),
                self.channel_name
            )
            print('---websocket debug info---   [in connect() with type INNER]   connected to user_id:' + str(
                parse_token(self.token)['user_id']))
            self.accept()

        elif self.type == TYPE_COUNT:
            self.token = self.scope['url_route']['kwargs']['token']
            user_id = parse_token(self.token)['user_id']
            async_to_sync(self.channel_layer.group_add)(
                'count' + str(user_id),
                self.channel_name
            )
            print('---websocket debug info---   [in connect() with type COUNT]   connected to user_id:' + str(
                parse_token(self.token)['user_id']))
            self.accept()

        else:
            self.disconnect(0)

    def disconnect(self, code):
        if self.type == TYPE_CHAT:
            async_to_sync(self.channel_layer.group_add)(
                str(self.chat_id),
                self.channel_name
            )
            print(
                '---websocket debug info---   [in disconnect() with type CHAT]   connected to chat_id:' + self.chat_id)

        if self.type == TYPE_INNER:
            async_to_sync(self.channel_layer.group_add)(
                str(parse_token(self.token)['user_id']),
                self.channel_name
            )
            print('---websocket debug info---   [in disconnect() with type INNER]   connected to user_id:' + str(
                parse_token(self.token)['user_id']))

        if self.type == TYPE_COUNT:
            async_to_sync(self.channel_layer.group_add)(
                'count' + str(parse_token(self.token)['user_id']),
                self.channel_name
            )
            print('---websocket debug info---   [in disconnect() with type COUNT]   connected to user_id:' + str(
                parse_token(self.token)['user_id']))

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        message = text_data_json['message']
        _token = text_data_json['token']
        message_type = text_data_json['message_type'] if 'message_type' in text_data_json else 'text'

        user_id = parse_token(_token)['user_id']
        user = get_user_by_id(user_id)

        if self.type == TYPE_CHAT:
            chat = Chat.objects.get(chat_id=self.chat_id)

            # store message
            storage_message = Message(message_description=message, message_from=user, message_to=chat,
                                      message_type=message_type)
            storage_message.save()

            chat_user_list = get_chat_user(chat)
            at_user_list = check_at(message, chat_user_list)

            print(chat_user_list)
            print(at_user_list)

            for single_user in chat_user_list:
                # 更新UserChat
                if UserChat.objects.filter(user=single_user, chat=chat):
                    user_chat = UserChat.objects.get(user=single_user, chat=chat)
                    user_chat.is_read = False
                    user_chat.save()
                else:
                    user_chat = UserChat(user=single_user, chat=chat, is_read=False)
                    user_chat.save()

                    # 更新UserMessage
                if UserMessage.objects.filter(user=single_user, message=storage_message):
                    user_message = UserMessage.objects.get(user=single_user, message=storage_message)
                    user_message.is_read = False
                    if 'at' in text_data_json and single_user in at_user_list:
                        user_message.is_at = True
                    user_message.save()
                else:
                    user_message = UserMessage(user=single_user, message=storage_message, is_read=False)
                    if 'at' in text_data_json and single_user in at_user_list:
                        user_message.is_at = True
                    user_message.save()

                if single_user in at_user_list:
                    print(single_user.user_nickname)
                    new_at = At(at_user=single_user, at_from=user, at_type='message', at_message=storage_message)
                    new_at.save()

                    # send inner message
                    data = new_at.info()
                    data['type'] = 'inner_message'
                    print(data)
                    async_to_sync(self.channel_layer.group_send)(
                        str(single_user.user_id),
                        data
                    )

                    # send count message
                    async_to_sync(self.channel_layer.group_send)(
                        'count' + str(single_user.user_id),
                        {
                            'type': 'count_message',
                            'num': str(get_unread_at_num(single_user))
                        }
                    )

            # send chat message
            async_to_sync(self.channel_layer.group_send)(
                str(self.chat_id),
                {
                    'type': 'chat_message',
                    'user_id': user.user_id,
                    'message_id': storage_message.message_id,
                    'message_title': storage_message.message_title,
                    'message': message,
                    'message_type': message_type,
                    'user_nickname': user.user_nickname,
                    'user_avatar': user.user_avatar,
                    'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'forward_type': storage_message.forward_type
                }
            )

        if self.type == TYPE_INNER:
            pass

        if self.type == TYPE_COUNT:
            pass

    def chat_message(self, event):
        message = event['message']
        message_id = event['message_id']
        message_type = event['message_type']
        message_title = event['message_title']
        user_nickname = event['user_nickname']
        user_avatar = event['user_avatar']
        time = event['time']
        short_time = event['time'][-5:]
        user_id = event['user_id']
        forward_type = event['forward_type']

        # 通过websocket发送消息到客户端
        self.send(text_data=json.dumps({
            'user_id': f'{user_id}',
            'chat_content': f'{message}',
            'message_type': f'{message_type}',
            'message_title': f'{message_title}',
            'user_name': f'{user_nickname}',
            'avatar': f'{user_avatar}',
            'post_time': f'{time}',
            'post_short_time': f'{short_time}',
            'message_id': f'{message_id}',
            'forward_type': f'{forward_type}'
        }))

        print('---websocket debug info---   [in chat_message()] broadcasting message to chat')

    def inner_message(self, event):
        message_id = event['message_id']
        message_from_name = event['message_from_name']
        message_time = event['message_time']
        message_content = event['message_content']
        at_type = event['at_type']
        if_read = event['if_read']

        # 通过websocket发送消息到客户端
        self.send(text_data=json.dumps({
            'message_id': f'{message_id}',
            'message_from_name': f'{message_from_name}',
            'message_time': f'{message_time}',
            'message_content': f'{message_content}',
            'type': f'{at_type}',
            'if_read': f'{if_read}',
        }))

        print('---websocket debug info---   [in inner_message()] broadcasting message to inner message center')

    def count_message(self, event):
        num = event['num']
        self.send(text_data=json.dumps({
            'num': f'{num}',
        }))

        print('---websocket debug info---   [in count_message()] broadcasting message to count message center')
