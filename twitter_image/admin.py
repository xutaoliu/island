from django.contrib import admin
from twitter_image.models import Task, TweetData, ImageData


admin.site.register([Task, TweetData, ImageData])
