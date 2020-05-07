from twitter_image.models import Task, TweetData, ImageData
from rest_framework import serializers


class TaskSerializer(serializers.ModelSerializer):
    tweets = serializers.HyperlinkedRelatedField(view_name='tweetdata-detail', many=True, read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'username', 'tag', 'last_update', 'tweets']


class TweetDataSerializer(serializers.ModelSerializer):
    task = serializers.HyperlinkedRelatedField(view_name='task-detail', many=False, read_only=True)

    class Meta:
        model = TweetData
        depth = 1
        fields = ['id', 'tweet', 'time', 'task', 'new', 'images']


class ImageDataSerializer(serializers.ModelSerializer):
    tweet = serializers.HyperlinkedRelatedField(view_name='tweetdata-detail', many=False, read_only=True)

    class Meta:
        model = ImageData
        fields = ['origin_url', 'image', 'tweet']
