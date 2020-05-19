from django.db import models


class BlockedAddress(models.Model):
    ip = models.GenericIPAddressField(primary_key=True)
    create_time = models.DateTimeField(auto_now_add=True)
