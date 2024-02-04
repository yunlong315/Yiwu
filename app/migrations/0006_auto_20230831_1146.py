# Generated by Django 3.2.3 on 2023-08-31 11:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20230831_1015'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='message_message',
        ),
        migrations.CreateModel(
            name='Forward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now=True)),
                ('forward_from', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forward_from', to='app.message')),
                ('froward_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forward_to', to='app.message')),
            ],
            options={
                'db_table': 'forward',
            },
        ),
    ]
