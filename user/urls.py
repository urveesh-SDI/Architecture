from django.contrib import admin
from django.urls import path
from . import views
from django.urls import path


urlpatterns = [
    path("signup",views.register.as_view()),
    path("login", views.login.as_view()), #as_view() is used to link with api or use api
    path("forgot",views.forgot.as_view()),
    path("ContactView",views.ContactView.as_view()),
    path("VerifyRegister",views.VerifyRegister.as_view()),
    path("Seekho",views.Seekho.as_view()),
    path("Verify_forgot",views.Verify_forgot.as_view()),
     path("user_info",views. user_info.as_view()),
    
]