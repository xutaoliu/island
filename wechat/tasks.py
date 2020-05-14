from celery import shared_task
from django.db import transaction
from twitter_image.models import Task
from django.utils import timezone


@shared_task
def update_task(user_id):
    with transaction.atomic():
        tasks = Task.objects.select_for_update(skip_locked=True).filter(owner_id=user_id)
        with timezone.override(None):
            for task in tasks:
                task.update(auto_flush_new=False)
                task.last_update = timezone.now()
                task.save()
