# Generated by Django 5.1.7 on 2025-04-01 07:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news_event', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='description',
        ),
        migrations.RemoveField(
            model_name='news',
            name='content',
        ),
    ]
