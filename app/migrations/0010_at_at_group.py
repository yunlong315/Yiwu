# Generated by Django 3.2.3 on 2023-09-01 14:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_auto_20230831_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='at',
            name='at_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.group'),
        ),
    ]
