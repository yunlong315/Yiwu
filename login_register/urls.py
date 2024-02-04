from django.urls import path
from login_register import views

urlpatterns = [
    path('users/register/', views.RegistrationCode.as_view()),
    path('users/register/confirm/', views.RegisterConfirm.as_view()),
    path('users/login/', views.Login.as_view()),
    path('password/forget/', views.ResetPassword.as_view()),
    path('password/reset/', views.ResetPasswordConfirm.as_view())
]
