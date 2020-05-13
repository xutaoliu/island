# Generated by Django 3.0.5 on 2020-05-13 09:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('twitter_image', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tweetdata',
            name='new',
        ),
        migrations.RemoveField(
            model_name='tweetdata',
            name='task',
        ),
        migrations.AlterField(
            model_name='imagedata',
            name='image',
            field=models.ImageField(null=True, upload_to='twitter_image'),
        ),
        migrations.CreateModel(
            name='TaskTweet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('new', models.BooleanField(default=True)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tweets', to='twitter_image.Task')),
                ('tweet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='twitter_image.TweetData')),
            ],
            options={
                'unique_together': {('task', 'tweet')},
            },
        ),
    ]
