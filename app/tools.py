import random
import string
from functools import wraps

import jwt
from django.core.mail import send_mail
from django.http import JsonResponse
from rest_framework import status
import os
import uuid
from django.conf import settings
import datetime
from jwt import exceptions

def create_token(user_id):
    payload = {
        'user_id': f'{user_id}',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def parse_token(token):
    # 需要在调用时处理过期异常
    return jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')


def get_user_id(request):
    token = request.META.get('HTTP_AUTHORIZATION')
    payload = parse_token(token)
    user_id = payload['user_id']
    return user_id

#
# def get_user(request):
#     user_id = get_user_id(request)
#     return User.objects.get(user_id=user_id)


def send_verification_email(email: str, type: str):
    # 生成随机验证码
    code = gen_confirm_code()

    # 发送邮件
    subject = f'协作平台{type}-验证码'
    message = f'您的验证码是：{code}\n验证码在十分钟后过期'
    recipient_list = [email]
    send_mail(subject=subject, message=message, from_email=None, recipient_list=recipient_list)

    # 返回验证码
    return code


def gen_confirm_code(length=6):
    """
    生成指定长度的随机字符型验证码
    """
    # 随机从数字和大小写字母中选择
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choice(chars) for _ in range(length))
    return code



def login_required_for_method(func):
    @wraps(func)
    def wrapper(apiview, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            return JsonResponse({'msg': "用户未登录"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            parse_token(token)
        except exceptions.ExpiredSignatureError:
            return JsonResponse({'msg': "登录过期"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(e)
            return JsonResponse({'msg': "token 错误"}, status=status.HTTP_401_UNAUTHORIZED)
        return func(apiview, request, *args, **kwargs)

    return wrapper


def login_required_for_function(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            return JsonResponse({'msg': "用户未登录"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            parse_token(token)
        except exceptions.ExpiredSignatureError:
            return JsonResponse({'msg': "登录过期"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(e)
            return JsonResponse({'msg': "token 错误"}, status=status.HTTP_401_UNAUTHORIZED)
        return func(request, *args, **kwargs)

    return wrapper






def random_avatar_path(instance, filename):
    # 获取文件的扩展名
    ext = filename.split('.')[-1]
    # 生成唯一的随机文件名
    random_name = uuid.uuid4().hex
    # 返回完整的文件路径
    return os.path.join('avatar', random_name + '.' + ext)
