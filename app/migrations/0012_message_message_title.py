# Generated by Django 3.2.3 on 2023-09-02 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_auto_20230902_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='message_title',
            field=models.TextField(default=''),
        ),
    ]