# Generated by Django 3.0.5 on 2020-06-03 02:35

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Proxy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField()),
                ('port', models.PositiveIntegerField(validators=[django.core.validators.MaxValueValidator(65535)])),
                ('protocol', models.CharField(choices=[('http', 'Http'), ('https', 'Https')], max_length=5)),
                ('anonymity', models.IntegerField(choices=[(0, 'No'), (1, 'High')])),
                ('site', models.URLField()),
                ('location', models.CharField(max_length=50)),
                ('delay', models.FloatField(default=-1)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'unique_together': {('ip', 'port')},
            },
        ),
    ]
