from django.urls import path
from . import views

urlpatterns = [
    path('create_document/', views.create_document),
    path('save_document/', views.save_document),
    path('delete_document/', views.delete_document),
    path('query_document/', views.query_document),
    path('query_project_document/', views.query_project_document),
    path('query_history_document/', views.query_history_document),
    path('at/', views.document_at),
    path('change_document_info/', views.change_document_info),
    path('create_directory/', views.create_directory),
    path('delete_directory/', views.delete_directory),
    path('rename_directory/', views.rename_directory),
    path('get_base_directory/', views.get_base_directory),
]
