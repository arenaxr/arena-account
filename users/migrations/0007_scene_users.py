# Generated by Django 3.1.14 on 2022-07-05 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_device'),
    ]

    operations = [
        migrations.AddField(
            model_name='scene',
            name='users',
            field=models.BooleanField(blank=True, default=True),
        ),
    ]
