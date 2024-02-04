from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_to_message),
    path('send_file/', views.send_file),
]
