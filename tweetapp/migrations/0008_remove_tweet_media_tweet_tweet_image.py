# Generated by Django 5.1.2 on 2024-12-06 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tweetapp', '0007_remove_tweet_tweet_image_tweet_media'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tweet',
            name='media',
        ),
        migrations.AddField(
            model_name='tweet',
            name='tweet_image',
            field=models.ImageField(blank=True, null=True, upload_to='tweet_images'),
        ),
    ]
