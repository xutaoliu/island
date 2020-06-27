from django.core.validators import MaxValueValidator
from django.db import models


class Proxy(models.Model):

    class Protocol(models.TextChoices):
        HTTP = 'http'
        HTTPS = 'https'

    class Anonymity(models.IntegerChoices):
        NO = 0
        HIGH = 1

    ip = models.GenericIPAddressField()
    port = models.PositiveIntegerField(validators=[MaxValueValidator(65535)])
    protocol = models.CharField(max_length=5, choices=Protocol.choices)
    anonymity = models.IntegerField(choices=Anonymity.choices)
    site = models.URLField()
    location = models.CharField(max_length=50)
    delay = models.FloatField(default=-1)
    last_update = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['ip', 'port']
