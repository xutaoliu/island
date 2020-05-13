from twitter_image.models import Task, ImageData, TaskTweet
from rest_framework import serializers


class TaskSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Task
        fields = ['id', 'username', 'tag', 'last_update', 'tweets']


class ImageDataSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = ImageData
        fields = ['origin_url', 'image', 'tweet']


class ImageRelatedField(serializers.RelatedField, serializers.ImageField):
    serializer = serializers.ImageField()

    def to_representation(self, value):
        return serializers.ImageField.to_representation(self, value.image)


class TaskTweetSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.CharField(source='tweet.id')
    tweet = serializers.CharField(source='tweet.tweet')
    time = serializers.DateTimeField(source='tweet.time')
    images = ImageRelatedField(source='tweet.images', many=True, read_only=True)

    class Meta:
        model = TaskTweet
        fields = ['task', 'id', 'tweet', 'time', 'new', 'images']
