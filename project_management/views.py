# Create your views here.
from django.db import transaction
from django.http import Http404, QueryDict
from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from app.models import *
from app.serializers import ProjectDetailSerializer, ProjectSerializer
from app.tools import login_required_for_method, login_required_for_function
from app.tools2 import get_user_id
import copy
from django.db.models import Q


class ProjectListOfGroup(APIView):
    ALLOWED_SORT_FIELDS = ['project_name', 'project_create_date', 'project_creator__user_name']
    ALLOWED_ORDER_FIELDS = ['asc', 'desc']

    @login_required_for_method
    # 获取团队中项目列表,可指定name_key查询参数查询包含name_key的项目,sort_key排序字段，order指定升序/降序
    def get(self, request, group_id):
        client_id = get_user_id(request)
        if UserGroup.objects.filter(user_id=client_id, group_id=group_id).exists() is False:
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        query_dict = QueryDict(request.GET.urlencode())
        name_key = query_dict.get('name_key', '')
        sort_by = query_dict.get('sort_key', '')
        order_by = query_dict.get('order', '')
        print(name_key, sort_by, order_by)
        if sort_by and sort_by not in self.ALLOWED_SORT_FIELDS:
            return JsonResponse({'msg': "Invalid order_by value"}, status=status.HTTP_400_BAD_REQUEST)

        if order_by and order_by not in self.ALLOWED_ORDER_FIELDS:
            return JsonResponse({'msg': "Invalid order_by value"}, status=status.HTTP_400_BAD_REQUEST)

        projects = Project.objects.filter(project_group_id=group_id, is_deleted=False, project_name__icontains=name_key)
        if sort_by and order_by:
            if order_by == 'asc':
                order_by = sort_by
            else:
                order_by = '-' + sort_by
            projects = projects.order_by(order_by,'-project_id')

        # project_name为空或为空字符串时，filter自动忽略该条件
        serializer = ProjectDetailSerializer(projects, many=True)
        res_data = {'project_list': serializer.data}
        return JsonResponse({'data': res_data})

    @login_required_for_method
    # 新建项目
    def post(self, request, group_id):
        client_id = get_user_id(request)
        if UserGroup.objects.filter(user_id=client_id, group_id=group_id).exists() is False:
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        data = {'project_name': request.data.get('project_name'), 'project_creator': client_id,
                'project_group': group_id}
        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            # create base directory
            base_dir = Directory(directory_name=request.data.get('project_name'), directory_project=serializer.instance)
            base_dir.save()

            return JsonResponse({'data': ProjectDetailSerializer(serializer.instance).data}, status=status.HTTP_200_OK)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectDetail(APIView):
    def get_object(self, project_id):
        try:
            return Project.objects.get(project_id=project_id, is_deleted=False)
        except Project.DoesNotExist:
            raise Http404

    @login_required_for_method
    # 获取项目详细信息
    def get(self, request, project_id):
        client_id = get_user_id(request)
        project = self.get_object(project_id=project_id)
        if UserGroup.objects.filter(user_id=client_id, group_id=project.project_group_id).exists() is False:
            print(client_id,project.project_group_id)
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProjectDetailSerializer(project)
        res_data = {'project': serializer.data}
        return JsonResponse({'data': res_data})

    @login_required_for_method
    # 修改项目信息
    def put(self, request, project_id):
        client_id = get_user_id(request)
        project = self.get_object(project_id=project_id)
        if UserGroup.objects.filter(user_id=client_id, group_id=project.project_group_id).exists() is False:
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        data = {'project_creator': project.project_creator_id, 'project_group': project.project_group_id,
                'project_name': request.data.get('project_name')}
        serializer = ProjectSerializer(project, data=data)
        if serializer.is_valid():
            serializer.save()
            res_data = {'project': serializer.data}
            return JsonResponse({'data': res_data})
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @login_required_for_method
    # 删除项目
    def delete(self, request, project_id):
        client_id = get_user_id(request)
        project = Project.objects.get(project_id=project_id)
        if UserGroup.objects.filter(user_id=client_id, group_id=project.project_group_id).exists() is False:
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
        if request.data.get('hard_delete') is True:
            project.delete()
            return JsonResponse({'msg': '已永久删除'}, status=status.HTTP_200_OK)
        else:
            if project.is_deleted:
                return JsonResponse({'msg': '项目已在回收站中'}, status=status.HTTP_400_BAD_REQUEST)
            project.soft_delete()
            return JsonResponse({'msg': '已放入回收站'}, status=status.HTTP_200_OK)


class TrashProjectList(APIView):
    @login_required_for_method
    # 获取回收站中项目
    def get(self, request, group_id):
        client_id = get_user_id(request)
        if UserGroup.objects.filter(user_id=client_id, group_id=group_id).exists() is False:
            return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)

        query_dict = QueryDict(request.GET.urlencode())
        name_key = query_dict.get('name_key', '')
        sort_by = query_dict.get('sort_key', '')
        order_by = query_dict.get('order', '')
        print(name_key, sort_by, order_by)
        if sort_by and sort_by not in self.ALLOWED_SORT_FIELDS:
            return JsonResponse({'msg': "Invalid order_by value"}, status=status.HTTP_400_BAD_REQUEST)

        if order_by and order_by not in self.ALLOWED_ORDER_FIELDS:
            return JsonResponse({'msg': "Invalid order_by value"}, status=status.HTTP_400_BAD_REQUEST)

        projects = Project.objects.filter(project_group_id=group_id, is_deleted=True, project_name__icontains=name_key)
        if sort_by and order_by:
            if order_by == 'asc':
                order_by = sort_by
            else:
                order_by = '-' + sort_by
            projects = projects.order_by(order_by,'-project_id')

        # project_name为空或为空字符串时，filter自动忽略该条件
        serializer = ProjectDetailSerializer(projects, many=True)
        res_data = {'project_list': serializer.data}
        return JsonResponse({'data': res_data})


## 从回收站中恢复项目
@api_view(['POST'])
@login_required_for_function
def project_recover(request, project_id):
    client_id = get_user_id(request)
    project = Project.objects.get(project_id=project_id)
    if UserGroup.objects.filter(user_id=client_id, group_id=project.project_group_id).exists() is False:
        return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
    if project.is_deleted is False:
        return JsonResponse({'msg': "项目不在回收站中"}, status=status.HTTP_404_NOT_FOUND)
    project.recover()
    return JsonResponse({'msg': '已从回收站恢复'}, status=status.HTTP_200_OK)


def create_project_copy(project_id,client_id):
    client = User.objects.get(user_id=client_id)
    # 创建Project副本
    with transaction.atomic():
        project = Project.objects.select_for_update().get(project_id=project_id, is_deleted=False)
        project.clone_times = project.clone_times + 1

        project_copy = copy.deepcopy(project)
        project_copy.project_id = None
        project_copy.clone_times = 0
        project_copy.project_name = f'{project.project_name}_副本{project.clone_times}'
        project_copy.project_creator = client
        project.save()
        project_copy.save()
        # 一级文件夹（根目录）
        directories = list(Directory.objects.filter(directory_project=project))

        directory_map = {}
        for directory in directories:
            directory_copy = copy.deepcopy(directory)
            directory_copy.directory_id = None
            if directory.directory_project:
                directory_copy.directory_project = project_copy
            else:
                directory_copy.directory_project = None
            directory_copy.save()  # 保存Directory副本
            directory_map[directory] = directory_copy

        # 二级文件夹
        second_directories = list(Directory.objects.filter(directory_directory__directory_project=project))
        for sd in second_directories:
            sd_copy = copy.deepcopy(sd)
            sd_copy.directory_id = None
            sd_copy.directory_directory = directory_map[sd.directory_directory]
            sd_copy.save()
            directory_map[sd] = sd_copy

        # 复制Document
        # 一级文件
        documents = list(Document.objects.filter(document_directory__directory_project=project))
        # 二级文件
        documents += list(Document.objects.filter(document_directory__directory_directory__directory_project=project))
        versions_id = []
        for d in documents:
            versions_id += DocumentVersion.objects.filter(dv_origin_document=d).values_list('dv_saved_document_id',
                                                                                            flat=True).distinct()
        documents += list(Document.objects.filter(document_id__in=versions_id))
        document_map = {}
        for document in documents:
            document_copy = copy.deepcopy(document)
            document_copy.document_id = None
            if document.document_directory:
                document_copy.document_directory = directory_map[document.document_directory]
            document_copy.save()  # 保存Document副本
            document_map[document] = document_copy

        # 复制DocumentVersion
        dvs = list(DocumentVersion.objects.filter(dv_origin_document__document_directory__directory_project=project))
        dvs += list(DocumentVersion.objects.filter(
            dv_origin_document__document_directory__directory_directory__directory_project=project))
        for dv in dvs:
            dv_copy = copy.deepcopy(dv)
            dv_copy.id = None
            dv_copy.dv_origin_document = document_map[dv.dv_origin_document]
            dv_copy.dv_saved_document = document_map[dv.dv_saved_document]
            dv_copy.save()  # 保存DocumentVersion副本

        # 复制Prototype
        prototypes = list(ProtoType.objects.filter(prototype_project=project))
        prototype_copies = []
        for prototype in prototypes:
            prototype_copy = copy.deepcopy(prototype)
            prototype_copy.prototype_id = None
            prototype_copy.prototype_project = project_copy
            prototype_copy.save()  # 保存Prototype副本
            prototype_copies.append(prototype_copy)

    return project_copy


# 创建项目副本
@api_view(['POST'])
@login_required_for_function
def project_copy(request, project_id):
    client_id = get_user_id(request)
    project = Project.objects.get(project_id=project_id)
    if UserGroup.objects.filter(user_id=client_id, group_id=project.project_group_id).exists() is False:
        return JsonResponse({'msg': "请求的资源不存在"}, status=status.HTTP_404_NOT_FOUND)
    project_copy = create_project_copy(project_id,client_id)
    serializer = ProjectDetailSerializer(project_copy)
    res_data = {'project': serializer.data}
    return JsonResponse({'data': res_data})
