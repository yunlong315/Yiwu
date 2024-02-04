import json

from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app.models import *
from app.serializers import UserSerializer
from django.http import Http404, QueryDict
from django.http.response import JsonResponse
from app.tools import send_verification_email, create_token
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseNotFound


class RegistrationCode(APIView):
    # 获取注册验证码
    def post(self, request):
        # 获取用户输入的邮箱
        user_email = request.data.get('user_email')
        if User.objects.filter(user_email=user_email).exists():
            return JsonResponse({'msg': "用户账号已存在"}, status=status.HTTP_400_BAD_REQUEST)
        code = send_verification_email(email=user_email, type="注册")
        new_cc = ConfirmCode(code=code, user_email=user_email)
        new_cc.save()
        # 返回成功响应
        return JsonResponse({'msg': '验证码已发送'}, status=status.HTTP_200_OK)


class RegisterConfirm(APIView):
    # 用户注册验证
    def post(self, request):
        user_email = request.data.get('user_email')
        if User.objects.filter(user_email=user_email).exists():
            return JsonResponse({'msg': "用户账号已存在"}, status=status.HTTP_400_BAD_REQUEST)
        confirm_code = request.data.get('confirm_code')
        cc_query = ConfirmCode.objects.filter(user_email=user_email)
        if cc_query.exists() is False:
            return JsonResponse({'msg': "未向该邮箱发送验证码"}, status=status.HTTP_404_NOT_FOUND)
        cc = cc_query.first()
        if confirm_code != cc.code:
            print(confirm_code,cc.code)
            return JsonResponse({'msg': "验证码错误"}, status=status.HTTP_400_BAD_REQUEST)
        if timezone.now() > cc.to_date:
            print(timezone.now(),cc.to_date)
            return JsonResponse({'msg': "验证码过期"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            res_data = {'user': serializer.data}
            return JsonResponse({'data': res_data}, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Login(APIView):
    # 登录
    def post(self, request):
        user_email = request.data.get('user_email')
        user_password = request.data.get('user_password')
        if User.objects.filter(user_email=user_email).exists() is False:
            return JsonResponse({'msg': "用户不存在"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(user_email=user_email)
        if check_password(user_password, user.user_password) is False:
            return JsonResponse({'msg': "密码错误"}, status=status.HTTP_400_BAD_REQUEST)
        token = create_token(user.user_id)
        res_data = {'token': token}
        return JsonResponse({'data': res_data}, status=status.HTTP_200_OK)


class ResetPassword(APIView):
    # 获取重置密码验证码
    def post(self, request):
        user_email = request.data.get('user_email')
        user_query = User.objects.filter(user_email=user_email)
        if user_query.exists() is False:
            return JsonResponse({'msg': "邮箱未绑定账号"}, status=status.HTTP_400_BAD_REQUEST)
        code = send_verification_email(user_email, type="找回账户/重置密码")
        new_rc = ResetCode(user_email=user_email, code=code)
        new_rc.save()
        return JsonResponse({'msg': '验证码已发送'}, status=status.HTTP_200_OK)


class ResetPasswordConfirm(APIView):
    # 重置密码
    def post(self, request):
        user_email = request.data.get('user_email')
        reset_code = request.data.get('reset_code')
        new_password = request.data.get('new_password')
        # 查询记录按时间降序排列
        rc_query = ResetCode.objects.filter(user_email=user_email)
        if rc_query.exists() is False:
            return JsonResponse({'msg': "验证码错误"})
        rc = rc_query.first()
        if rc.code != reset_code:
            return JsonResponse({'msg': "验证码错误"}, status=status.HTTP_400_BAD_REQUEST)
        User.objects.filter(user_email=user_email).update(user_password=make_password(new_password))
        return JsonResponse({'msg': "修改密码成功"}, status=status.HTTP_200_OK)
