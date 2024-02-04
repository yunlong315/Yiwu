from django.urls import path
from . import views

urlpatterns = [
    path('create_prototype/', views.create_prototype),
    path('save_prototype/', views.save_prototype),
    path('query_prototype/', views.query_prototype),
    path('delete_prototype/', views.delete_prototype),
    path('query_project_prototype/', views.query_project_prototype),
    path('change_prototype_info/', views.change_prototype_info),
    path('preview/<int:project_id>/',views.PrototypePreview.as_view()),
    path('preview/detail/',views.PreviewDetail.as_view())
]
