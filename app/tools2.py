import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from app.models import *
from app.tools import get_user_id


def get_data(request):
    print(
        '---debug info---   [in app.tools2.get_data()]   request.path:' + str(request.path) + '   request.body:' + str(
            request.body))
    if request.body:
        return json.loads(request.body.decode('utf-8'))
    return None


def get_user(request):
    user_id = get_user_id(request)
    return User.objects.get(user_id=user_id)


def query_checker(query_str, whole_str):
    return query_str in whole_str


def get_chat_user(chat):
    return list(set(x.user for x in list(UserChat.objects.filter(chat=chat))))


key = 42


def encrypt(user_id):
    encrypted_id = ''.join(chr(ord(c) ^ key) for c in str(user_id))
    return str(user_id)


def decrypt(encrypted_id):
    decrypted_id = ''.join(chr(ord(c) ^ key) for c in encrypted_id)
    return encrypted_id


def get_unread_at_num(user: User):
    unread_at_list = At.objects.filter(at_user=user, is_read=False)
    return len(unread_at_list)


def resend_to_chat():
    pass


def resend_to_inner():
    pass


def resend_to_count(user: User):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'count' + str(user.user_id),
        {
            'type': 'count_message',
            'num': str(get_unread_at_num(user))
        }
    )

