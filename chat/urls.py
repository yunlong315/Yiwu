from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('get_history/', views.get_history_message),
    path('get_message_center/', views.get_message_center),
    path('get_chat_list/', views.get_chat_list),
    path('get_single_chat/', views.get_single_chat),
    path('set_chat_read/', views.set_chat_read),
    path('set_message_read/', views.set_message_read),
    path('create_chat/', views.create_chat),
    path('create_private_chat/', views.create_private_chat),
    path('join_chat/', views.join_chat),
    path('quit_chat/', views.quit_chat),
    path('dismiss_chat/', views.dismiss_chat),
    path('kick_from_chat/', views.kick_from_chat),
    path('set_chat_read/', views.set_chat_read),
    path('set_message_read/', views.set_message_read),
    path('set_message_all_read/', views.set_message_all_read),
    path('delete_message/', views.delete_message),
    path('query_message/', views.query_message),
    path('query_single_message/', views.query_single_message),
    path('delete_all_read_at/', views.delete_all_read_at),
    path('set_at_read/', views.set_at_read),
    path('delete_at/', views.delete_at),
    path('read_all_at/', views.read_all_at),
    path('get_group_chat/', views.get_chat_in_group),
    path('get_user_id/', views.get_user_id),
    path('invite_to_chat/', views.invite_to_chat),
    path('forward/', views.forward),
    path('get_combined_forward/', views.get_combined_forward),
    path('get_chat_user_list/', views.get_chat_user_list),
    path('jump_to_chat/', views.jump_to_chat),
    path('jump_to_document/', views.jump_to_document),
    path('<str:room_name>/', views.room),
    path('2/<str:room_name>/', views.room2),
]
