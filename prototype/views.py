from app.tools import *
from app.tools2 import *
from rest_framework.views import APIView
from app.serializers import PrototypeSerializer


@login_required_for_function
def create_prototype(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    prototype_name = data.get('prototype_name')
    prototype_description = data.get('prototype_description')
    prototype_project = Project.objects.get(project_id=data.get('prototype_project_id'))
    prototype_creator = get_user(request)
    if UserGroup.objects.filter(user=prototype_creator, group=prototype_project.project_group).exists() is False:
        return JsonResponse({'msg': "你不在团队中"}, status=status.HTTP_404_NOT_FOUND)
    prototype_content = {}
    new_prototype = ProtoType(prototype_name=prototype_name, prototype_project=prototype_project,
                              prototype_creator=prototype_creator, prototype_description=prototype_description,
                              prototype_content=prototype_content)
    new_prototype.save()

    print('---debug info---   [in create_prototype()]   prototype_id: ' + str(
        new_prototype.prototype_id) + '   prototype_name:  ' + new_prototype.prototype_name)

    return JsonResponse({'prototype_id': new_prototype.prototype_id}, status=status.HTTP_200_OK)


@login_required_for_function
def save_prototype(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    prototype_id = data.get('prototype_id')
    prototype_content = data.get('prototype_content')

    if not ProtoType.objects.filter(prototype_id=prototype_id):
        return JsonResponse({'msg': "原型不存在"}, status=status.HTTP_400_BAD_REQUEST)
    prototype = ProtoType.objects.get(prototype_id=prototype_id)
    if UserGroup.objects.filter(user=user, group=prototype.prototype_project.project_group).exists() is False:
        return JsonResponse({'msg': "你不在团队中"}, status=status.HTTP_404_NOT_FOUND)
    prototype.prototype_content = prototype_content
    prototype.save()

    print('---debug info---   [in save_prototype()]   prototype_id: ' + str(
        prototype.prototype_id) + '   prototype_name:  ' + prototype.prototype_name)

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def delete_prototype(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    prototype_id = data.get('prototype_id')
    if not ProtoType.objects.filter(prototype_id=prototype_id):
        return JsonResponse({'msg': "原型不存在"}, status=status.HTTP_400_BAD_REQUEST)
    prototype = ProtoType.objects.get(prototype_id=prototype_id)
    if UserGroup.objects.filter(user=user, group=prototype.prototype_project.project_group).exists() is False:
        return JsonResponse({'msg': "你不在团队中"}, status=status.HTTP_404_NOT_FOUND)
    prototype.delete()

    print('---debug info---   [in delete_prototype()]   prototype_id: ' + str(
        prototype.prototype_id) + '   prototype_name:  ' + prototype.prototype_name)

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def query_prototype(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    prototype_id = data.get('prototype_id')
    if not ProtoType.objects.filter(prototype_id=prototype_id):
        return JsonResponse({'msg': "原型不存在"}, status=status.HTTP_400_BAD_REQUEST)
    prototype = ProtoType.objects.get(prototype_id=prototype_id)
    if UserGroup.objects.filter(user=user, group=prototype.prototype_project.project_group).exists() is False:
        return JsonResponse({'msg': "你不在团队中"}, status=status.HTTP_404_NOT_FOUND)
    print('---debug info---   [in query_prototype()]   prototype_id: ' + str(
        prototype.prototype_id) + '   prototype_name:  ' + prototype.prototype_name)

    return JsonResponse({'data': {
        'prototype_id': prototype.prototype_id,
        'prototype_project_id': prototype.prototype_project.project_id,
        'prototype_creator_id': prototype.prototype_creator.user_id,
        'prototype_name': prototype.prototype_name,
        'prototype_description': prototype.prototype_description,
        'prototype_content': prototype.prototype_content
    }}, status=status.HTTP_200_OK)


@login_required_for_function
def query_project_prototype(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    client_id = get_user_id(request)
    data = get_data(request)
    project = Project.objects.get(project_id=data.get('project_id'))
    if UserGroup.objects.filter(user_id=client_id, group_id=project.project_group_id).exists() is False:
        return JsonResponse({'msg': "你不在团队中"}, status=status.HTTP_404_NOT_FOUND)
    prototype_list = list(ProtoType.objects.filter(prototype_project=project))
    data = [{
        'prototype_id': x.prototype_id,
        'prototype_project': x.prototype_project.project_id,
        'prototype_name': x.prototype_name,
        'prototype_creator': x.prototype_creator.user_id,
        'prototype_content': x.prototype_content,
        'prototype_description': x.prototype_description
    } for x in prototype_list]

    print('---debug info---   [in query_project_prototype()]   project_id: ' + str(
        project.project_id) + '   returning ' + str(len(data)) + ' prototypes')

    return JsonResponse({'data': data}, status=status.HTTP_200_OK)


@login_required_for_function
def change_prototype_info(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    user = get_user(request)
    prototype_id = data.get('prototype_id')

    if not ProtoType.objects.filter(prototype_id=prototype_id):
        return JsonResponse({'msg': "没有这个原型"}, status=status.HTTP_400_BAD_REQUEST)

    prototype = ProtoType.objects.get(prototype_id=prototype_id)
    if UserGroup.objects.filter(user=user, group=prototype.prototype_project.project_group).exists() is False:
        return JsonResponse({'msg': "你不在团队中"}, status=status.HTTP_404_NOT_FOUND)
    if 'prototype_name' in data:
        prototype.prototype_name = data.get('prototype_name')
    if 'prototype_description' in data:
        prototype.prototype_description = data.get('prototype_description')
    if 'prototype_content' in data:
        prototype.prototype_content = data.get('prototype_content')

    prototype.save()

    print('---debug info---   [in query_project_prototype()]   prototype_id: ' + str(prototype.prototype_id))

    return JsonResponse({}, status=status.HTTP_200_OK)


class PrototypePreview(APIView):
    # 获取演示地址，如果没有开启演示,则is_open返回false
    @login_required_for_method
    def get(self, request, project_id):
        client_id = get_user_id(request)
        project = Project.objects.get(project_id=project_id)
        if UserGroup.objects.filter(user_id=client_id, group_id=project.project_group_id).exists() is False:
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        preview_query = Preview.objects.filter(project_id=project_id)
        if preview_query.exists():
            res_data = {'is_open': True,
                        'preview_url': f'http://101.42.5.240/preview?project_id={project_id}&code={preview_query.first().code}'}
            return JsonResponse({'data': res_data})
        else:
            res_data = {'is_open': False, 'preview_url': ''}
            return JsonResponse({'data': res_data})

    # 开启演示
    @login_required_for_method
    def post(self, request, project_id):
        client_id = get_user_id(request)
        project = Project.objects.get(project_id=project_id)
        if UserGroup.objects.filter(user_id=client_id, group_id=project.project_group_id).exists() is False:
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        preview_query = Preview.objects.filter(project_id=project_id)
        if preview_query.exists():
            res_data = {'is_open': True,
                        'preview_url': f'http://101.42.5.240/preview?project_id={project_id}&code={preview_query.first().code}'}
            return JsonResponse({'data': res_data})
        new_preview = Preview(project_id=project_id, code=gen_confirm_code(length=8))
        new_preview.save()
        res_data = {'is_open': True,
                    'preview_url': f'http://101.42.5.240/preview?project_id={project_id}&code={new_preview.code}'}
        return JsonResponse({'data': res_data})

    # 关闭演示
    @login_required_for_method
    def delete(self, request, project_id):
        client_id = get_user_id(request)
        project = Project.objects.get(project_id=project_id)
        if UserGroup.objects.filter(user_id=client_id, group_id=project.project_group_id).exists() is False:
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        try:
            preview = Preview.objects.get(project_id=project_id)
        except Preview.DoesNotExist:
            return JsonResponse({'msg': "演示关闭成功"}, status=status.HTTP_200_OK)
        preview.delete()
        return JsonResponse({'msg': "演示关闭成功"}, status=status.HTTP_200_OK)


class PreviewDetail(APIView):
    # 获取preview信息
    def get(self, request):
        project_id = request.GET.get('project_id', None)
        code = request.GET.get('code', None)
        if code is None or Preview.objects.filter(project_id=project_id, code=code).exists() is False:
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        prototypes = ProtoType.objects.filter(prototype_project_id=project_id)
        serializer = PrototypeSerializer(prototypes, many=True)
        res_data = {'prototype_list': serializer.data}
        return JsonResponse({'data': res_data}, status=status.HTTP_200_OK)
