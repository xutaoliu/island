"""island URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from island import settings
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
import wechat.views

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    path('api-token/', obtain_jwt_token, name='login'),
    path('api-token/refresh/', refresh_jwt_token),
    path('twitter_image/', include('twitter_image.urls')),
    path('wechat/', wechat.views.serve),
]
