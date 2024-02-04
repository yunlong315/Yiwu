from django.urls import path
from project_management import views

urlpatterns = [
    path('group/<int:group_id>/projects/', views.ProjectListOfGroup.as_view()),
    path('project/<int:project_id>/', views.ProjectDetail.as_view()),
    path('group/<int:group_id>/trash/',views.TrashProjectList.as_view()),
    path('project/<int:project_id>/recover/',views.project_recover),
    path('project/<int:project_id>/copy/',views.project_copy)
]
