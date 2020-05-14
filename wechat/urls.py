from django.urls import re_path, path
from wechat import views

urlpatterns = [
    path('', views.serve),
    re_path(r'imgs/(?P<imgs>.+)$', views.serve_imgs, name='wechat_imgs')
]
