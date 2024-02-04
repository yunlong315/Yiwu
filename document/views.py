from app.tools import *
from app.tools2 import *


@login_required_for_function
def create_document(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    directory_id = data.get('directory_id')
    user = get_user(request)
    title = data.get('title')
    content = data.get('content') if 'content' in data else ''

    directory = Directory.objects.get(directory_id=directory_id)

    document = Document(document_directory=directory, document_creator=user, document_title=title,
                        document_content=content)
    document.save()

    print('---debug info---   [in create_document()]   document_id: ' + str(
        document.document_id) + '   document_title: ' + str(document.document_title))

    return JsonResponse({'document_id': document.document_id}, status=status.HTTP_200_OK)


@login_required_for_function
def save_document(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    document_id = data.get('document_id')
    document_title = data.get('document_title')
    document_content = data.get('document_content')
    saver = get_user(request)

    if not Document.objects.filter(document_id=document_id):
        return JsonResponse({'msg': "没有这个文档"}, status=status.HTTP_400_BAD_REQUEST)
    document = Document.objects.get(document_id=document_id)

    document.document_title = document_title
    document.document_content = document_content
    document.save()

    # 保存历史版本
    saved_document = Document(document_creator=document.document_creator,
                              document_title=document.document_title,
                              document_content=document.document_content)
    saved_document.save()

    document_version = DocumentVersion(dv_origin_document=document, dv_saved_document=saved_document, dv_saver=saver)
    document_version.save()

    print('---debug info---   [in save_document()]   document_id: ' + str(
        document.document_id) + '   document_title: ' + str(document.document_title))

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def delete_document(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    document_id = data.get('document_id')
    if not Document.objects.filter(document_id=document_id):
        return JsonResponse({'msg': "没有这个文档"}, status=status.HTTP_400_BAD_REQUEST)
    document = Document.objects.get(document_id=document_id)
    document.delete()

    print('---debug info---   [in delete_document()]   document_id: ' + str(
        document.document_id) + '   document_title: ' + str(document.document_title))

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def query_document(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)
    document_id = data.get('document_id')
    if not Document.objects.filter(document_id=document_id):
        return JsonResponse({'msg': "没有这个文档"}, status=status.HTTP_400_BAD_REQUEST)
    document = Document.objects.get(document_id=document_id)

    print('---debug info---   [in query_document()]   document_id: ' + str(
        document.document_id) + '   document_title: ' + str(document.document_title))

    return JsonResponse({
        'document_id': document.document_id,
        'document_creator': document.document_creator.user_id,
        'document_title': document.document_title,
        'document_content': document.document_content
    }, status=status.HTTP_200_OK)


@login_required_for_function
def query_project_document(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    project = Project.objects.get(project_id=data.get('project_id'))
    base_dir = Directory.objects.get(directory_project=project)

    secondary_dir_list = list(Directory.objects.filter(directory_directory=base_dir))

    data_dir = []
    data_doc = get_document_list_dict_in_dir(base_dir)
    for secondary_dir in secondary_dir_list:
        data_dir.append({
            'name': secondary_dir.directory_name,
            'dir_id': secondary_dir.directory_id,
            'documents': get_document_list_dict_in_dir(secondary_dir)
        })

    print('---debug info---   [in query_document()]   project_id: ' + str(project.project_id) + '   returning ' + str(
        len(data_doc)) + ' documents   ' + str(len(data_dir)) + ' directories')

    return JsonResponse({
        'directories': data_dir,
        'documents': data_doc
    }, status=status.HTTP_200_OK)


def get_document_list_dict_in_dir(directory):
    return [{
        'document_id': x.document_id,
        'document_creator': x.document_creator.user_id,
        'document_title': x.document_title,
        'document_content': x.document_content,
        'document_directory': x.document_directory.directory_id
    } for x in list(Document.objects.filter(document_directory=directory))]


@login_required_for_function
def query_history_document(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    document_id = data.get('document_id')

    document = Document.objects.get(document_id=document_id)
    history_document_list = [{
        'document_id': x.dv_saved_document.document_id,
        'document_creator': x.dv_saved_document.document_creator.user_id,
        'document_title': x.dv_saved_document.document_title,
        'document_content': x.dv_saved_document.document_content,
        'document_time': x.dv_time.strftime('%Y-%m-%d %H:%M:%S')
    } for x in list(DocumentVersion.objects.filter(dv_origin_document=document))]
    history_document_list = sorted(history_document_list, key=lambda x: x['document_time'], reverse=True)

    print('---debug info---   [in query_history_document()]   document_id: ' + str(document_id) + '   returning ' + str(
        len(history_document_list)) + ' histories')

    return JsonResponse({'history_document_list': history_document_list}, status=status.HTTP_200_OK)


def get_project_by_id(proj_id):
    return Project.objects.get(project_id=proj_id)


@login_required_for_function
def document_at(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    document = Document.objects.get(document_id=data.get('document_id'))
    user_from = get_user(request)
    user_to = User.objects.get(user_id=data.get('user_id'))

    new_at = At(at_user=user_to, at_from=user_from, at_type='document', at_document=document)
    new_at.save()

    print('---debug info---   [in document_at()]   document_id: ' + str(document.document_id) + '   @ user ' + str(user_to.user_id) + ' ' + user_to.user_nickname)

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def change_document_info(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    document_id = data.get('document_id')

    if not Document.objects.filter(document_id=document_id):
        return JsonResponse({'msg': "没有这个文档"}, status=status.HTTP_400_BAD_REQUEST)

    document = Document.objects.get(document_id=document_id)

    if 'document_title' in data:
        document.document_title = data.get('document_title')
    if 'document_content' in data:
        document.document_content = data.get('document_content')

    document.save()

    print('---debug info---   [in change_document_info()]   document_id: ' + str(document.document_id))

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def create_directory(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    base_dir = Directory.objects.get(directory_id=data.get('base_directory_id'))
    directory_name = data.get('directory_name')

    new_dir = Directory(directory_name=directory_name, directory_directory=base_dir)
    new_dir.save()

    return JsonResponse({
        'directory_id': new_dir.directory_id,
        'directory_name': new_dir.directory_name
    }, status=status.HTTP_200_OK)


@login_required_for_function
def delete_directory(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    directory = Directory.objects.get(directory_id=data.get('directory_id'))

    if directory.directory_project is not None:
        return JsonResponse({'msg': "不能删除根目录"}, status=status.HTTP_400_BAD_REQUEST)

    directory.delete()

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def rename_directory(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    directory = Directory.objects.get(directory_id=data.get('directory_id'))
    new_name = data.get('new_name')

    if directory.directory_project is not None:
        return JsonResponse({'msg': "不能重命名根目录"}, status=status.HTTP_400_BAD_REQUEST)

    directory.directory_name = new_name
    directory.save()

    return JsonResponse({}, status=status.HTTP_200_OK)


@login_required_for_function
def get_base_directory(request):
    if request.method != 'POST':
        return JsonResponse({'msg': "请求方式错误"}, status=status.HTTP_400_BAD_REQUEST)
    data = get_data(request)

    project = Project.objects.get(project_id=data.get('project_id'))

    base_dir = Directory.objects.get(directory_project=project)

    return JsonResponse({
        'directory_id': base_dir.directory_id,
        'directory_name': base_dir.directory_name,
    }, status=status.HTTP_200_OK)
