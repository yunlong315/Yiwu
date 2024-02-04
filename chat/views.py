from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from app.models import *
from app.tools import *
from app.tools2 import *
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer


def index(request):
    return render(request, 'chat/index.html', {})


def room(request, room_name):
    return render(request, 'chat/room.html', {
        'room_name': room_name
    })


def room2(request, room_name):
    return render(request, 'chat/room2.html', {
        'room_name': room_name
    })


DEFAULT_MESSAGE_NUM = 20


@login_required_for_function
def get_history_message(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    user = get_user(request)
    chat = Chat.objects.get(chat_id=data.get('chat_id'))

    history_messages = [x for x in list(Message.objects.filter(message_to=chat))
                        if UserMessage.objects.filter(user=user, message=x, is_deleted=False)]

    history_messages = sorted(history_messages, key=lambda x: x.message_time.__str__(), reverse=True)

    # check for file upload
    for history_message in history_messages:
        if history_message.message_type != 'text' and history_message.message_description == '' and history_message.forward_type != 'combined':
            history_messages.remove(history_message)

    # 判断加载模式
    if 'up_message_id' in data and 'down_message_id' in data:
        return JsonResponse({'msg': "加载模式错误"}, status=status.HTTP_400_BAD_REQUEST)
    if 'up_message_id' in data:
        end_message = Message.objects.get(message_id=data.get('up_message_id'))
        end_index = history_messages.index(end_message) + 1
        start_index = 0
        if end_index == 0:
            return JsonResponse({'data': []}, status=status.HTTP_200_OK)
        history_messages = history_messages[start_index: end_index]
    if 'down_message_id' in data:
        start_message = Message.objects.get(message_id=data.get('down_message_id'))
        start_index = history_messages.index(start_message) + 1
        end_index = start_index + DEFAULT_MESSAGE_NUM if start_index + DEFAULT_MESSAGE_NUM <= len(
            history_messages) else len(history_messages)
        if start_index == len(history_messages) - 1:
            return JsonResponse({'data': []}, status=status.HTTP_200_OK)
        history_messages = history_messages[start_index: end_index]

    res = [x.info() for x in history_messages]

    if len(res) > DEFAULT_MESSAGE_NUM:
        res = res[:DEFAULT_MESSAGE_NUM]

    print(
        '---debug info---   [in chat.views.get_history_message()]   in chat:' + chat.chat_name + ' returning {} messages:'.format(
            len(res)))
    # print('---debug info---   [in chat.views.get_history_message()]   returning messages:' + str(res))

    return JsonResponse({'data': res}, status=status.HTTP_200_OK)


@login_required_for_function
def get_message_center(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    user = get_user(request)
    user_at_list = [x for x in list(At.objects.filter(at_user=user))]
    read_list = []
    unread_list = []
    invitation_list = []

    for user_at in user_at_list:
        if user_at.is_read:
            if user_at.at_type == 'message':
                read_list.append(user_at.info())
            if user_at.at_type == 'document':
                read_list.append(user_at.info())
            if user_at.at_type == 'invitation':
                invitation_list.append(user_at.info())
        else:
            if user_at.at_type == 'message':
                unread_list.append(user_at.info())
            if user_at.at_type == 'document':
                unread_list.append(user_at.info())
            if user_at.at_type == 'invitation':
                invitation_list.append(user_at.info())
    read_list = sorted(read_list, key=lambda x: x['message_time'], reverse=True)
    unread_list = sorted(unread_list, key=lambda x: x['message_time'], reverse=True)
    return JsonResponse({
        'read_list': read_list,
        'unread_list': unread_list,
        'invitation_list': invitation_list
    }, status=status.HTTP_200_OK)


def get_latest_message(chat):
    msgs = list(Message.objects.filter(message_to=chat))
    msgs = sorted(msgs, key=lambda x: x.message_time.__str__())
    return {
        'message_description': msgs[-1].message_description,
        'message_time': msgs[-1].message_time.__str__()
    }


def get_user_id(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    payload = parse_token(token)
    user_id = payload['user_id']
    return JsonResponse({'user_id': user_id}, status=status.HTTP_200_OK)


@login_required_for_function
def create_chat(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    user = get_user(request)
    data = get_data(request)

    chat_name = data.get('chat_name') if 'chat_name' in data else generate_chat_name()
    chat_description = data.get('chat_description')

    chat = Chat(chat_name=chat_name, chat_description=chat_description, chat_owner=user,)
    chat.chat_type = data.get('chat_type')
    chat.save()
    chat.save()
    user_chat = UserChat(user=user, chat=chat)
    user_chat.save()

    return JsonResponse({
        'chat_id': chat.chat_id
    }, status=status.HTTP_200_OK)


@login_required_for_function
def create_private_chat(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    user = get_user(request)
    other_user = User.objects.get(user_id=data.get('user_id'))

    chat = already_have_private_chat(user, other_user)
    if chat is not None:
        return JsonResponse({
            'chat_id': chat.chat_id
        }, status=status.HTTP_200_OK)

    chat = Chat(chat_type='private')
    chat.save()

    user_chat1 = UserChat(user=user, chat=chat)
    user_chat1.save()

    user_chat2 = UserChat(user=other_user, chat=chat)
    user_chat2.save()

    return JsonResponse({
        'chat_id': chat.chat_id
    }, status=status.HTTP_200_OK)


def already_have_private_chat(user1: User, user2: User):
    user1_private_chats = [x.chat for x in list(UserChat.objects.filter(user=user1)) if x.chat.chat_type == 'private']
    user2_private_chats = [x.chat for x in list(UserChat.objects.filter(user=user2)) if x.chat.chat_type == 'private']

    common_private_chats = list(set(user1_private_chats) & set(user2_private_chats))

    if len(common_private_chats) > 0:
        return common_private_chats[0]

    return None


def generate_chat_name():
    name = ''
    while Chat.objects.filter(chat_name=name) and name != '':
        name = ''.join(random.choice(string.ascii_letters) for _ in range(128))
    return name


@login_required_for_function
def join_chat(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    user = get_user(request)
    data = get_data(request)

    if not At.objects.filter(at_id=data.get('at_id')) or At.objects.get(at_id=data.get('at_id')).at_type != 'invitation':
        return JsonResponse({'msg': "未收到邀请"}, status=status.HTTP_400_BAD_REQUEST)

    at = At.objects.get(at_id=data.get('at_id'))

    chat = at.at_chat

    at.delete()

    # check if already in chat
    if UserChat.objects.filter(user=user, chat=chat):
        return JsonResponse({'msg': "已加入群聊"}, status=status.HTTP_400_BAD_REQUEST)

    resend_to_count(user)

    user_chat = UserChat(user=user, chat=chat)
    user_chat.save()
    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def quit_chat(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    user = get_user(request)
    data = get_data(request)
    chat = Chat.objects.get(chat_id=data.get('chat_id'))
    if not UserChat.objects.filter(user=user, chat=chat):
        return JsonResponse({'msg': "未加入群聊"}, status=status.HTTP_400_BAD_REQUEST)
    user_chat = UserChat.objects.get(user=user, chat=chat)
    user_chat.delete()
    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def get_chat_list(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    public_chat_list = [{
        'chat_id': x.chat.chat_id,
        'chat_name': x.chat.chat_name,
        'chat_display_name': get_chat_name(x.chat, user),
        'chat_avatar': get_chat_avatar(x.chat, user).__str__(),
        'chat_description': x.chat.chat_description,
        'is_read': True if x.is_read else False,
        'chat_type': x.chat.chat_type,
        'time': get_latest_message_time(x.chat),
        'is_admin': x.chat.chat_owner == user
    } for x in list(UserChat.objects.filter(user=user)) if x.chat.chat_type == 'public']
    public_chat_list = sorted(public_chat_list, key=lambda x: x['is_read'])

    private_chat_list = [{
        'chat_id': x.chat.chat_id,
        'chat_name': x.chat.chat_name,
        'chat_display_name': get_chat_name(x.chat, user),
        'chat_avatar': get_chat_avatar(x.chat, user).__str__(),
        'chat_description': x.chat.chat_description,
        'is_read': True if x.is_read else False,
        'chat_type': x.chat.chat_type,
        'time': get_latest_message_time(x.chat),
        'is_admin': x.chat.chat_owner == user
    } for x in list(UserChat.objects.filter(user=user))if x.chat.chat_type == 'private']
    private_chat_list = sorted(private_chat_list, key=lambda x: x['is_read'])

    default_chat_list = [{
        'chat_id': x.chat.chat_id,
        'chat_name': x.chat.chat_name,
        'chat_display_name': get_chat_name(x.chat, user),
        'chat_avatar': get_chat_avatar(x.chat, user).__str__(),
        'chat_description': x.chat.chat_description,
        'is_read': True if x.is_read else False,
        'chat_type': x.chat.chat_type,
        'time': get_latest_message_time(x.chat),
        'is_admin': x.chat.chat_owner == user
    } for x in list(UserChat.objects.filter(user=user)) if x.chat.chat_type == 'default']
    default_chat_list = sorted(default_chat_list, key=lambda x: x['is_read'])

    chat_list = public_chat_list + private_chat_list
    chat_list = sorted(chat_list, key=lambda x: x['time'], reverse=True)

    all_chat_list = public_chat_list + private_chat_list + default_chat_list
    all_chat_list = sorted(all_chat_list, key=lambda x: x['time'], reverse=True)

    return JsonResponse({
        'chat_list': chat_list,
        'all_chat_list': all_chat_list
    }, status=status.HTTP_200_OK)


@login_required_for_function
def get_single_chat(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    chat = Chat.objects.get(chat_id=data.get('chat_id'))
    user = get_user(request)

    data = {
        'chat_id': chat.chat_id,
        'chat_name': chat.chat_name,
        'chat_display_name': get_chat_name(chat, user),
        'chat_avatar': get_chat_avatar(chat, user).__str__(),
        'chat_description': chat.chat_description,
        'is_read': True,
        'chat_type': chat.chat_type,
        'time': get_latest_message_time(chat),
        'is_admin': True if chat.chat_owner == user else False
    }

    return JsonResponse({
        'data': data
    }, status=status.HTTP_200_OK)


def get_latest_message_time(chat):
    message_list = list(Message.objects.filter(message_to=chat))
    message_list = sorted(message_list, key=lambda x: x.message_time.__str__(), reverse=True)
    if len(message_list) == 0:
        return ''
    return message_list[0].message_time.__str__()


def get_chat_name(chat, user):
    if chat.chat_type == 'public':
        return chat.chat_name
    if chat.chat_type == 'private':
        other_user = UserChat.objects.filter(chat=chat).exclude(user=user)[0].user
        return other_user.user_nickname
    if chat.chat_type == 'default':
        return chat.chat_name


def get_chat_avatar(chat, user):
    if chat.chat_type == 'public':
        return chat.chat_avatar
    if chat.chat_type == 'private':
        other_user = UserChat.objects.filter(chat=chat).exclude(user=user)[0].user
        return other_user.user_avatar
    if chat.chat_type == 'default':
        return chat.chat_avatar


@login_required_for_function
def set_chat_read(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    chat = Chat.objects.get(chat_id=data.get('chat_id'))
    if UserChat.objects.filter(user=user, chat=chat):
        user_chat = UserChat.objects.get(user=user, chat=chat)
        user_chat.is_read = True
        user_chat.save()
        return JsonResponse({}, status=status.HTTP_200_OK)
    else:
        return JsonResponse({'msg': '未加入群聊'}, status=status.HTTP_400_BAD_REQUEST)


@login_required_for_function
def set_message_read(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    message = Message.objects.get(message_id=data.get('message_id'))
    if UserMessage.objects.filter(user=user, message=message):
        user_message = UserMessage.objects.get(user=user, message=message)
        user_message.is_read = True
        user_message.save()
        return JsonResponse({}, status=status.HTTP_200_OK)
    else:
        return JsonResponse({'msg': '你不应该见到这个消息'}, status=status.HTTP_400_BAD_REQUEST)


@login_required_for_function
def set_message_all_read(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    user_chat_list = list(UserChat.objects.filter(user=user))
    for user_chat in user_chat_list:
        user_chat.is_read = True
        user_chat.save()
    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def delete_message(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    message = data.get('message_id')
    if not UserMessage.objects.filter(user=user, message=message):
        return JsonResponse({'msg': '消息不存在'}, status=status.HTTP_400_BAD_REQUEST)
    user_message = UserMessage.objects.get(user=user, message=message)
    user_message.is_deleted = True
    user_message.save()
    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def query_message(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    query_str = data.get('query_str')

    # 判断检索模式
    message_list = [x.message for x in list(UserMessage.objects.filter(user=user, is_deleted=False))]

    if 'chat_id' in data:
        chat = Chat.objects.get(chat_id=data.get('chat_id'))
        message_list = [x for x in message_list if x.message_to == chat]

    message_list = sorted(message_list, key=lambda x: x.message_time.__str__(), reverse=True)

    res = [{
        'message_id': x.message_id,
        'message_from': x.message_from.user_nickname,
        'message_to': x.message_to.chat_id,
        'message_time': x.message_time.strftime('%Y-%m-%d %H:%M'),
        'message_description': x.message_description
    } for x in message_list if query_checker(query_str, x.message_description)]

    return JsonResponse({'data': res}, status=status.HTTP_200_OK)


@login_required_for_function
def delete_all_read_at(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)

    at_list = list(At.objects.filter(at_user=user, is_read=True))

    for at in at_list:
        at.delete()

    # send count message
    resend_to_count(user)

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def set_at_read(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)

    at_id = data.get('at_id')

    at = At.objects.get(at_id=at_id)
    at.is_read = True
    at.save()

    # send count message
    resend_to_count(user)

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def delete_at(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    at_id = data.get('at_id')
    user = get_user(request)

    if not At.objects.filter(at_id=at_id):
        return JsonResponse({'msg': "没有这条@消息"}, status=status.HTTP_400_BAD_REQUEST)
    at = At.objects.get(at_id=at_id)
    if at.at_user != user:
        return JsonResponse({'msg': "不是你的@消息"}, status=status.HTTP_400_BAD_REQUEST)
    at.delete()

    # send count message
    resend_to_count(user)

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def read_all_at(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)

    user = get_user(request)

    at_list = list(At.objects.filter(at_user=user))
    for at in at_list:
        at.is_read = True
        at.save()

    # send count message
    resend_to_count(user)

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def get_chat_in_group(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    group = Group.objects.get(group_id=data.get('group_id'))
    chat = Chat.objects.get(chat_group__group_id=data.get('group_id'))
    res = {
        'chat_id': chat.chat_id,
        'chat_name': chat.chat_name,
        'chat_avatar': chat.chat_avatar,
        'chat_description': chat.chat_description,
        'is_read': UserChat.objects.filter(user=user, chat=chat, is_read=True).exists(),
        'chat_group_id': chat.chat_group.group_id,
        'is_admin': True if UserGroup.objects.filter(user=user, group=group, identity__in=['admin', 'creator']) else False
    }
    return JsonResponse({"data": res}, status=status.HTTP_200_OK)


@login_required_for_function
def invite_to_chat(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    chat = Chat.objects.get(chat_id=data.get('chat_id'))
    email = data.get('email')
    from_user = get_user(request)

    if not User.objects.filter(user_email=email):
        return JsonResponse({'msg': "邮箱未注册"}, status=status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)

    invite_list = [User.objects.get(user_email=email)]

    for user in invite_list:
        # check if already joined
        if UserChat.objects.filter(user=user, chat=chat):
            return JsonResponse({'msg': "已发送邀请"}, status=status.HTTP_423_LOCKED)
        # check if already invited
        if At.objects.filter(at_user=user, at_type='invitation', at_chat=chat):
            continue

        new_at = At(at_from=from_user, at_user=user, at_type='invitation', at_chat=chat)
        new_at.save()

        data = {
            'type': 'inner_message',
            'message_id': new_at.at_id,
            'message_from_id': chat.chat_id,  # chat_id
            'message_from_name': chat.chat_name,  # chat_name
            'message_time': new_at.at_time.strftime('%Y-%m-%d %H:%M'),
            'message_content': 'chat',
            'at_type': 'chat_invitation',
            'if_read': False,
        }

        my_layer = get_channel_layer()
        # send websocket messages
        async_to_sync(my_layer.group_send)(
            str(user.user_id),
            data
        )

        resend_to_count(user)

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def dismiss_chat(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    chat = Chat.objects.get(chat_id=data.get('chat_id'))
    user = get_user(request)

    if chat.chat_type == 'default':
        return JsonResponse({'msg': "不能解散团队默认群聊"}, status=status.HTTP_400_BAD_REQUEST)

    if chat.chat_owner != user:
        return JsonResponse({'msg': "只有群主能解散群聊"}, status=status.HTTP_400_BAD_REQUEST)

    chat.delete()

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def forward(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    forward_type = data.get('forward_type')
    message_list = [Message.objects.get(message_id=x) for x in data.get('message_list')]
    chat = Chat.objects.get(chat_id=data.get('chat_id'))
    user = get_user(request)

    message_list = sorted(message_list, key=lambda x: x.message_time.__str__())

    # forward by item, excluded from table 'Forward'
    if forward_type == 'item':
        for message in message_list:
            new_message = Message(message_description=message.message_description, message_from=user, message_to=chat, message_type=message.message_type, forward_type=message.forward_type)

            # if new_message.forward_type == 'combined':
            #     ori_list = [x.forward_from for x in list(Forward.objects.filter(froward_to=message))]
            #     for ori in ori_list:
            #         new_forward = Forward(forward_from=ori, froward_to=new_message)
            #         new_forward.save()

            save_message(user, chat, new_message)
            broadcast_message(user, chat, new_message)

    # forward combined, included in table 'Forward'
    if forward_type == 'combined':
        combined_message = Message(message_from=user, message_to=chat, forward_type='combined')
        save_message(user, chat, combined_message)
        broadcast_message(user, chat, combined_message)

        # update 'Forward'
        for message in message_list:
            cur_forward = Forward(forward_from=message, froward_to=combined_message)
            cur_forward.save()

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def get_combined_forward(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    message = Message.objects.get(message_id=data.get('message_id'))

    if message.forward_type != 'combined':
        return JsonResponse({'msg': "不是合并转发消息"}, status=status.HTTP_400_BAD_REQUEST)

    data = [x.forward_from.info() for x in list(Forward.objects.filter(froward_to=message))]

    return JsonResponse({'data': data}, status=status.HTTP_200_OK)


def save_message(user: User, chat: Chat, message: Message):
    message.save()

    chat_user_list = get_chat_user(chat)

    for _user in chat_user_list:
        user_message = UserMessage(user=_user, message=message)
        user_message.save()


def broadcast_message(user: User, chat: Chat, message: Message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        str(chat.chat_id),
        {
            'type': 'chat_message',
            'user_id': user.user_id,
            'message_id': message.message_id,
            'message': message.message_description,
            'message_title': message.message_title,
            'message_type': message.message_type,
            'user_nickname': user.user_nickname,
            'user_avatar': user.user_avatar,
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'forward_type': message.forward_type
        }
    )


@login_required_for_function
def query_single_message(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    message = Message.objects.get(message_id=data.get('message_id'))
    user = get_user(request)

    if not UserMessage.objects.filter(user=user, message=message, is_deleted=False):
        return JsonResponse({'msg': "没有这个消息"}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'data': message.info()}, status=status.HTTP_200_OK)


@login_required_for_function
def get_chat_user_list(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    user = get_user(request)
    chat = Chat.objects.get(chat_id=data.get('chat_id'))

    if not UserChat.objects.filter(user=user, chat=chat):
        return JsonResponse({'msg': "没有这个群聊"}, status=status.HTTP_400_BAD_REQUEST)

    data = [x.user for x in list(set(UserChat.objects.filter(chat=chat)))]
    data.remove(user)
    data.insert(0, user)
    data = [x.info() for x in data]

    return JsonResponse({'data': data}, status=status.HTTP_200_OK)


@login_required_for_function
def kick_from_chat(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    user_from = get_user(request)
    user_to = User.objects.get(user_id=data.get('user_id'))
    chat = Chat.objects.get(chat_id=data.get('chat_id'))

    if chat.chat_owner != user_from:
        return JsonResponse({'msg': "没有权限"}, status=status.HTTP_400_BAD_REQUEST)

    if not UserChat.objects.filter(user=user_to, chat=chat):
        return JsonResponse({'msg': "用户未加入群聊"}, status=status.HTTP_400_BAD_REQUEST)

    user_chat = UserChat.objects.get(user=user_to, chat=chat)
    user_chat.delete()

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def jump_to_chat(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    at = At.objects.get(at_id=data.get('at_id'))

    group_id = -1
    if at.at_message.message_to.chat_type == 'default':
        group_id = at.at_message.message_to.chat_group.group_id

    res = {
        'chat_id': at.at_message.message_to.chat_id,
        'message_id': at.at_message.message_id,
        'group_id': group_id,
    }

    return JsonResponse({'data': res}, status=status.HTTP_200_OK)


@login_required_for_function
def jump_to_document(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    at = At.objects.get(at_id=data.get('at_id'))

    res = {
        'group_id': get_group_id(at),
        'project_id': get_project_id(at),
        'doc_id': at.at_document.document_id,
    }

    return JsonResponse({'data': res}, status=status.HTTP_200_OK)


def get_group_id(at: At):
    base_directory = at.at_document.document_directory
    if base_directory.directory_directory is not None:
        base_directory = base_directory.directory_directory
    project = base_directory.directory_project
    return project.project_group.group_id


def get_project_id(at: At):
    base_directory = at.at_document.document_directory
    if base_directory.directory_directory is not None:
        base_directory = base_directory.directory_directory
    return base_directory.directory_project.project_id
