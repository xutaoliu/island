from django.db import models
import twint
from island import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import requests
import os
import logging

logger = logging.getLogger('twitter_image')


class Task(models.Model):
    username = models.CharField(max_length=50)
    tag = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    last_update = models.DateTimeField(default=timezone.make_aware(timezone.datetime.utcfromtimestamp(0), timezone=timezone.utc))

    def search_tweets(self):
        tweets = []
        c = twint.Config()
        c.Username = self.username
        c.Since = self.last_update.date().strftime('%Y-%m-%d %H:%M:%S')
        c.Proxy_host = settings.PROXY_HOST
        c.Proxy_port = settings.PROXY_PORT
        c.Proxy_type = settings.PROXY_TYPE
        c.Search = self.tag
        c.Store_object = True
        c.Store_object_tweets_list = tweets
        twint.run.Search(c)
        return tweets

    def update(self, auto_flush_new=True):
        tweets = self.search_tweets()
        logger.info(f'Task {self.id} get tweets: {len(tweets)}')
        if auto_flush_new:
            TweetData.objects.filter(new=True).update(new=False)
        for tweet in tweets:
            if not TweetData.objects.filter(id=tweet.id).exists():
                tweet_data = TweetData.objects.create(id=tweet.id, task=self, tweet=tweet.tweet, time=timezone.make_aware(timezone.datetime.strptime(f'{tweet.datestamp} {tweet.timestamp}', '%Y-%m-%d %H:%M:%S')))
                for photo in tweet.photos:
                    img_data = ImageData(origin_url=photo, tweet=tweet_data)
                    img_data.update()
                    img_data.save()


class TweetData(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='tweets')
    tweet = models.CharField(max_length=200)
    time = models.DateTimeField()
    new = models.BooleanField(default=True)


class ImageData(models.Model):
    origin_url = models.URLField(unique=True)
    image = models.ImageField(null=True)
    tweet = models.ForeignKey(TweetData, on_delete=models.CASCADE, related_name='images')

    def update(self):
        try:
            result = requests.get(self.origin_url, proxies={
                'http': f'{settings.PROXY_TYPE}://{settings.PROXY_HOST}:{settings.PROXY_PORT}',
                'https': f'{settings.PROXY_TYPE}://{settings.PROXY_HOST}:{settings.PROXY_PORT}'
            }, timeout=5)
            if result.status_code == 200:
                with NamedTemporaryFile() as img_temp:
                    img_temp.write(result.content)
                    img_temp.flush()
                    self.image.save(os.path.basename(self.origin_url), File(img_temp), save=False)
                    return True
        except requests.exceptions.RequestException as e:
            logger.warning(f'[Image Download Failed]: {self.origin_url} {e.args}')
        return False
