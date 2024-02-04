from asgiref.sync import async_to_sync
from django.http import Http404
from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from channels.layers import get_channel_layer

from app.models import *
from app.serializers import UserSerializer, GroupSerializer, UserGroupSerializer, UserGroupDetailSerializer, \
    ChatSerializer
from app.tools import login_required_for_method, get_user_id, login_required_for_function
from app.tools2 import get_user
from django.db import transaction, DatabaseError


class UserDetail(APIView):
    def get_object(self, user_id):
        try:
            return User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise Http404

    # 获取指定用户
    def get(self, request, user_id):
        user = self.get_object(user_id=user_id)
        serializer = UserSerializer(user)
        res_data = {'user': serializer.data}
        return JsonResponse({'data': res_data})

    # 更新指定用户信息
    @login_required_for_method
    def put(self, request, user_id):
        client_id = get_user_id(request)

        if user_id != int(client_id):
            print(client_id, user_id)
            return JsonResponse({'msg': '不能更改他人信息'}, status=status.HTTP_400_BAD_REQUEST)
        user = self.get_object(user_id=user_id)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            res_data = {'user': serializer.data}
            return JsonResponse({'data': res_data})
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 删除指定用户
    @login_required_for_method
    def delete(self, request, user_id):
        # 获取当前登录的用户
        client_id = get_user_id(request)
        if user_id != client_id:
            JsonResponse({'msg': '只有用户自己能注销自己'}, status=status.HTTP_403_FORBIDDEN)
        # 获取要删除的用户
        user = self.get_object(user_id=user_id)
        user.delete()
        return JsonResponse({'msg': '删除成功'}, status=status.HTTP_204_NO_CONTENT)


class GroupListOfUser(APIView):
    # 用户创建团队
    @login_required_for_method
    def post(self, request):
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                group_id = serializer.data.get('group_id')
                user_group_data = {'user': get_user_id(request), 'group': group_id,
                                   'identity': UserGroup.TEAM_CREATOR}
                ug_serializer = UserGroupSerializer(data=user_group_data)
                if ug_serializer.is_valid():
                    ug_serializer.save()
                else:
                    return JsonResponse(ug_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    # 创建一个默认群聊
                group = Group.objects.get(group_id=group_id)
                group_name = group.group_name
                chat_data = {'chat_name': f"{group_name}默认群聊", "chat_description": f"{group_name}的默认群聊",
                             "chat_group": group_id, 'chat_type': 'default'}
                chat_serializer = ChatSerializer(data=chat_data)
                if chat_serializer.is_valid():
                    # 用户自己加入默认群聊
                    chat_serializer.save()
                    user = get_user(request)
                    user_chat = UserChat(user=user, chat=chat_serializer.instance, is_read=True)
                    user_chat.save()
                    return JsonResponse({'data': serializer.data}, status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse(chat_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 用户所在团队列表
    @login_required_for_method
    def get(self, request):
        user_id = get_user_id(request)
        user_groups = UserGroup.objects.filter(user_id=user_id)
        groups = Group.objects.filter(usergroup__in=user_groups)
        serializer = GroupSerializer(groups, many=True)
        res_data = {'group_list': serializer.data}
        return JsonResponse({'data': res_data})


class GroupDetail(APIView):
    def get_object(self, group_id):
        try:
            return Group.objects.get(group_id=group_id)
        except Group.DoesNotExist:
            return JsonResponse({'msg': "没有该团队"}, status=status.HTTP_400_BAD_REQUEST)

    # 获取团队详情
    @login_required_for_method
    def get(self, request, group_id):
        user_id = get_user_id(request)
        if UserGroup.objects.filter(user_id=user_id, group_id=group_id).exists() is False:
            return JsonResponse({'msg': "不在该团队中"}, status=status.HTTP_400_BAD_REQUEST)
        group = self.get_object(group_id=group_id)
        user_groups = UserGroup.objects.filter(group_id=group_id)
        res_data = {'group': GroupSerializer(group).data,
                    'user_list': UserGroupDetailSerializer(user_groups, many=True).data,
                    'my_identity': UserGroup.objects.get(user_id=user_id, group_id=group_id).identity}
        return JsonResponse({'data': res_data})

    # 修改团队信息,需要管理员权限
    @login_required_for_method
    def put(self, request, group_id):
        user_id = get_user_id(request)
        client_ug = UserGroup.objects.filter(user_id=user_id, group_id=group_id)
        if client_ug.exists() is False:
            return JsonResponse({'msg': "不在该团队中"}, status=status.HTTP_400_BAD_REQUEST)
        client_ug = client_ug.first()
        if client_ug.identity == UserGroup.TEAM_MEMBER:
            return JsonResponse({'msg': "没有权限"}, status=status.HTTP_400_BAD_REQUEST)
        group = self.get_object(group_id=group_id)
        serializer = GroupSerializer(group, data=request.data)
        if serializer.is_valid():
            serializer.save()

            group = client_ug.group
            chat = Chat.objects.get(chat_group=group)
            chat.chat_name = group.group_name + '默认群聊'
            chat.chat_description = group.group_name + '的默认群聊'
            chat.save()

            res_data = {'group': serializer.data}
            return JsonResponse({'data': res_data})
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 解散团队，需要创建者权限
    @login_required_for_method
    def delete(self, request, group_id):
        user_id = get_user_id(request)
        client_ug = UserGroup.objects.filter(user_id=user_id, group_id=group_id)
        if client_ug.exists() is False:
            return JsonResponse({'msg': "不在该团队中"}, status=status.HTTP_400_BAD_REQUEST)
        client_ug = client_ug.first()
        if client_ug.identity != UserGroup.TEAM_CREATOR:
            return JsonResponse({'msg': "没有权限"}, status=status.HTTP_400_BAD_REQUEST)
        group = self.get_object(group_id=group_id)
        group.delete()
        return JsonResponse({'msg': '删除成功'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['post'])
@login_required_for_function
def accept_invitation(request):
    user = get_user(request)
    at_id = request.data.get('at_id')
    try:
        at = At.objects.get(at_id=at_id)
        group = at.at_group
    except At.DoesNotExist:
        return JsonResponse({'msg': "没有这条邀请"}, status=status.HTTP_404_NOT_FOUND)
    if UserGroup.objects.filter(user=user, group=group).exists():
        return JsonResponse({'msg': "你已在该团队中"})
    ug_data = {'user': user.user_id, 'group': group.group_id}
    serializer = UserGroupSerializer(data=ug_data)
    if serializer.is_valid():
        with transaction.atomic():
            serializer.save()
            at.delete()
            relate_ats = At.objects.filter(at_user=user, at_group=group)
            relate_ats.delete()
            # 加入默认群聊
            default_chat = Chat.objects.get(chat_group=group)
            user_chat = UserChat(user=user, chat=default_chat)
            user_chat.save()
        return JsonResponse({'msg': "加入团队成功"})
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from chat.views import resend_to_count


class GroupMember(APIView):
    # 邀请成员进入团队,需要管理员权限
    @login_required_for_method
    def post(self, request):
        client = get_user(request)
        user_email = request.data.get('user_email')
        group_id = request.data.get('group_id')
        try:
            # 检查存在性
            client_ug = UserGroup.objects.get(user_id=client.user_id, group_id=group_id)
            group = Group.objects.get(group_id=group_id)
            target = User.objects.get(user_email=user_email)
        except (User.DoesNotExist, Group.DoesNotExist, UserGroup.DoesNotExist):
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        if client_ug.identity == UserGroup.TEAM_MEMBER:
            return JsonResponse({'msg': "没有权限"}, status=status.HTTP_400_BAD_REQUEST)
        if UserGroup.objects.filter(user=target, group=group).exists():
            return JsonResponse({'msg': "已在团队中"})
        if At.objects.filter(at_user=target, at_group=group).exists():
            return JsonResponse({'msg': "已邀请过"})
        # ug_data = {'user': target.user_id, 'group': group_id}
        # serializer = UserGroupSerializer(data=ug_data)
        if True:  # serializer.is_valid()
            # serializer.save()
            # 新用户加入默认群聊
            user = User.objects.get(user_id=target.user_id)
            chat = Chat.objects.get(chat_group_id=group_id)
            # user_chat = UserChat(user=user, chat=chat, is_read=True)
            # user_chat.save()

            # send websocket message
            new_at = At(at_from=client_ug.user, at_user=user, at_type='invitation', at_group=group)
            new_at.save()
            channel_layer = get_channel_layer()
            data = {
                'type': 'inner_message',
                'message_id': new_at.at_id,
                'message_from_id': group.group_id,  # chat_id
                'message_from_name': group.group_name,  # chat_name
                'message_time': new_at.at_time.strftime('%Y-%m-%d %H:%M'),
                'message_content': 'group',
                'at_type': new_at.at_type,
                'if_read': False,
            }
            async_to_sync(channel_layer.group_send)(
                str(user.user_id),
                data
            )

            resend_to_count(user)

            return JsonResponse({'msg': '邀请成功'}, status=status.HTTP_200_OK)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 从团队中移除成员
    # 将普通成员移除团队：管理员权限。
    # 将管理员移除团队：创建者权限。
    def delete(self, request):
        client = get_user(request)
        group_id = request.data.get('group_id')
        user_id = request.data.get('user_id')
        try:
            # 检查存在性
            client_ug = UserGroup.objects.get(user_id=client.user_id, group_id=group_id)
            group = Group.objects.get(group_id=group_id)
            target = User.objects.get(user_id=user_id)
            target_ug = UserGroup.objects.get(user_id=user_id, group_id=group_id)
        except (User.DoesNotExist, Group.DoesNotExist, UserGroup.DoesNotExist):
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)

        if client_ug.identity == UserGroup.TEAM_MEMBER:
            return JsonResponse({'msg': "没有权限"}, status=status.HTTP_400_BAD_REQUEST)
        if target_ug.identity == UserGroup.TEAM_ADMIN and client_ug.identity != UserGroup.TEAM_CREATOR:
            return JsonResponse({'msg': "没有权限"}, status=status.HTTP_400_BAD_REQUEST)
        if target_ug.identity == UserGroup.TEAM_CREATOR:
            return JsonResponse({'msg': "不能删除创建者"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                target_ug.delete()
                # 从默认群聊中移除成员
                user_chat = UserChat.objects.get(user_id=user_id, chat__chat_group_id=group_id)
                user_chat.delete()
                return JsonResponse({'msg': '删除成功'}, status=status.HTTP_200_OK)
        except DatabaseError as e:
            # 处理数据库错误
            return JsonResponse({'msg': '删除失败，数据库错误', 'error': str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # 处理其他异常
            return JsonResponse({'msg': '删除失败，其他异常', 'error': str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 更改成员权限
    # 普通->管理员, 管理员权限
    # 管理员->普通，创建者权限
    # 不能更改创建者
    def put(self, request):
        client = get_user(request)
        group_id = request.data.get('group_id')
        user_id = request.data.get('user_id')
        try:
            # 检查存在性
            client_ug = UserGroup.objects.get(user_id=client.user_id, group_id=group_id)
            group = Group.objects.get(group_id=group_id)
            target = User.objects.get(user_id=user_id)
            target_ug = UserGroup.objects.get(user_id=user_id, group_id=group_id)
        except (User.DoesNotExist, Group.DoesNotExist, UserGroup.DoesNotExist):
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)

        if client_ug.identity == UserGroup.TEAM_MEMBER:
            return JsonResponse({'msg': "没有权限"}, status=status.HTTP_400_BAD_REQUEST)
        if target_ug.identity == UserGroup.TEAM_ADMIN and client_ug.identity != UserGroup.TEAM_CREATOR:
            return JsonResponse({'msg': "没有权限"}, status=status.HTTP_400_BAD_REQUEST)
        if target_ug.identity == UserGroup.TEAM_CREATOR:
            return JsonResponse({'msg': "没有权限"}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('identity') == UserGroup.TEAM_CREATOR:
            return JsonResponse({'msg': "不能将权限修改为创建者"}, status=status.HTTP_400_BAD_REQUEST)

        data = {'user': user_id, 'group': group_id, 'identity': request.data.get('identity')}
        serializer = UserGroupSerializer(target_ug, data=data)
        if serializer.is_valid():
            serializer.save()
            res_data = {'user_group': serializer.data}
            return JsonResponse({'data': res_data})
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


## 根据token获取用户自己
@api_view(['get'])
@login_required_for_function
def get_myself(request):
    user = get_user(request)
    serializer = UserSerializer(user)
    res_data = {'user': serializer.data}
    return JsonResponse({'data': res_data})


## 检查用户是否在团队内
@api_view(['get'])
@login_required_for_function
def check_in_group(request, group_id):
    client_id = get_user_id(request)
    res_data = {'is_in_group': UserGroup.objects.filter(user_id=client_id, group_id=group_id).exists()}
    return JsonResponse({'data': res_data})


## 检查用户是否在项目内
@api_view(['get'])
@login_required_for_function
def check_in_project(request, project_id):
    client_id = get_user_id(request)
    try:
        group_id = Project.objects.get(project_id=project_id).project_group_id
    except Project.DoesNotExist:
        return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
    res_data = {'is_in_project': UserGroup.objects.filter(user_id=client_id, group_id=group_id).exists()}
    return JsonResponse({'data': res_data})
