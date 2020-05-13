from django.urls import include, path
from rest_framework import routers
from twitter_image import views

router = routers.DefaultRouter()
router.register('tasks', views.TaskViewSet, basename='task')
router.register('tweets', views.TaskTweetViewSet, basename='tasktweet')

urlpatterns = [
    path('', include(router.urls))
]
