from django.db import models
from django.contrib.auth.models import User


class WechatUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    openid = models.CharField(max_length=50, primary_key=True)
    subscribe_time = models.DateTimeField()


class Message(models.Model):

    class Trigger(models.TextChoices):
        TEXT = 'text'

    id = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(WechatUser, on_delete=models.CASCADE)
    time = models.DateTimeField()
    type = models.CharField(max_length=10, choices=Trigger.choices)


class TextMessage(models.Model):
    message = models.OneToOneField(Message, on_delete=models.CASCADE, primary_key=True, related_name='body')
    content = models.CharField(max_length=200)
