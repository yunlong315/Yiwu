from django.urls import path
from staff_management import views

urlpatterns = [
    path('users/<int:user_id>/', views.UserDetail.as_view()),
    path('user/groups/', views.GroupListOfUser.as_view()),
    path('group/<int:group_id>/', views.GroupDetail.as_view()),
    path('group/user/', views.GroupMember.as_view()),
    path('myself/', views.get_myself),
    path('check_in_group/<int:group_id>/', views.check_in_group),
    path('check_in_project/<int:project_id>/', views.check_in_project),
    path('join_group/',views.accept_invitation)
]
