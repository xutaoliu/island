from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from island.exceptions import PermissionDenied, ServiceUnavailable, APIException
from twitter_image.models import Task, TweetData, ImageData
from twitter_image.serializers import TaskSerializer, TweetDataSerializer, ImageDataSerializer
from aiohttp.client_exceptions import ClientError
from asyncio import TimeoutError
import logging

logger = logging.getLogger('twitter_image')


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['username', 'tag']
    search_fields = ['tag']
    ordering_fields = ['last_update']
    ordering = ['-last_update']

    @action(detail=True, methods=['patch'])
    def refresh(self, request, pk=None):
        try:
            with transaction.atomic():
                task = Task.objects.select_for_update(skip_locked=True).get(pk=pk)
                if task.owner != request.user:
                    raise PermissionDenied()
                with timezone.override(None):
                    task.update()
                    task.last_update = timezone.now()
                task.save()
            serializer = TaskSerializer(task, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (ClientError, TimeoutError) as e:
            logger.error('[Proxy Down]', exc_info=e)
            raise ServiceUnavailable()
        except BaseException as e:
            logger.fatal('[Unknow Error]', exc_info=e)
            raise APIException()


class TweetDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TweetData.objects.all()
    serializer_class = TweetDataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['task__username', 'new']
    search_fields = ['tweet']
    ordering_fields = ['time', 'new']
    ordering = ['-time']


class ImageDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ImageData.objects.all()
    serializer_class = ImageDataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['tweet__new']
    search_fields = ['tweet__tweet']
    ordering_fields = ['tweet__time', 'tweet__new']
    ordering = ['-tweet__time']

    @action(detail=True, methods=['patch'])
    def refresh(self, request, pk=None):
        try:
            with transaction.atomic():
                image = ImageData.objects.select_for_update(skip_locked=True).get(pk=pk)
                if image.image:
                    return Response(status=status.HTTP_204_NO_CONTENT)
                image.update()
                image.save()
            serializer = TaskSerializer(image, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ClientError as e:
            logger.error('[Proxy Down]', exc_info=e)
            raise ServiceUnavailable()
        except BaseException as e:
            logger.fatal('[Unknow Error]', exc_info=e)
            raise APIException()
