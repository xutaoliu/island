from django.urls import include, path
from rest_framework import routers
from twitter_image import views

router = routers.DefaultRouter()
router.register('tasks', views.TaskViewSet)
router.register('tweets', views.TweetDataViewSet)
router.register('images', views.ImageDataViewSet)

urlpatterns = [
    path('', include(router.urls))
]
