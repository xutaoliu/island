from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from island.exceptions import PermissionDenied, ServiceUnavailable, APIException
from twitter_image.models import Task, TweetData, ImageData, TaskTweet
from twitter_image.serializers import TaskSerializer, TaskTweetSerializer, ImageDataSerializer
from aiohttp.client_exceptions import ClientError
from asyncio import TimeoutError
import logging

logger = logging.getLogger('twitter_image')


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['username', 'tag']
    search_fields = ['tag']
    ordering_fields = ['last_update']
    ordering = ['-last_update']

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

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


class TaskTweetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskTweetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['new', 'task']
    search_fields = ['tweet__tweet']
    ordering_fields = ['tweet__time']
    ordering = ['-tweet__time']

    def get_queryset(self):
        return TaskTweet.objects.filter(task__owner=self.request.user)
