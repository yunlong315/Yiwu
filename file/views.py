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
from chat.views import save_message


BASE_IP = 'http://101.42.5.240:9091/media'


def upload_to_message(request):
    # sent a decoy message identified by 'message_id' before upload the file
    # the decoy message is sent by front end
    file = request.FILES['file']
    message_id = request.POST.get('message_id')

    message_title = ''
    if 'message_title' in request.POST:
        message_title = request.POST.get('message_title')

    message = Message.objects.get(message_id=message_id)
    real_name = file.name
    _, file_extension = os.path.splitext(real_name)

    saved_file = File(file=file, real_name=real_name, type=file_type_mapping(file_extension))
    saved_file.save()

    message.message_description = BASE_IP + saved_file.file.url
    message.message_type = file_type_mapping(file_extension)
    message.message_title = real_name
    save_message(message.message_from, message.message_to, message)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        str(message.message_to.chat_id),
        {
            'type': 'chat_message',
            'user_id': message.message_from.user_id,
            'message_id': message.message_id,
            'message_title': message.message_title,
            'message': message.message_description,
            'message_type': message.message_type,
            'user_nickname': message.message_from.user_nickname,
            'user_avatar': message.message_from.user_avatar,
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'forward_type': message.forward_type
        }
    )

    return JsonResponse({
        'path': BASE_IP + saved_file.file.url,
        'real_name': saved_file.real_name,
        'type': saved_file.type
    }, status=status.HTTP_200_OK)


@login_required_for_function
def send_file(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    user = get_user(request)
    chat = Chat.objects.get(chat_id=data.get('chat_id'))

    message = Message(message_description='', message_from=user, message_to=chat, message_type='file')
    message.save()

    return JsonResponse({
        'user_id': message.message_from.user_id,
        'message_id': message.message_id,
        'message': message.message_description,
        'message_type': message.message_type,
        'user_nickname': message.message_from.user_nickname,
        'user_avatar': message.message_from.user_avatar.url,
        'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'forward_type': message.forward_type
    }, status=status.HTTP_200_OK)


def file_type_mapping(file_extension):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    video_extensions = ['.mp4', '.avi', '.mkv']

    if file_extension.lower() in image_extensions:
        return 'image'
    elif file_extension.lower() in video_extensions:
        return 'video'
    else:
        return 'file'
