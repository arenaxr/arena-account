# Generated by Django 3.2.25 on 2025-01-09 19:16

from django.conf import settings
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0007_scene_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='scene',
            name='owners',
            field=models.ManyToManyField(blank=True, related_name='scene_owners', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='scene',
            name='viewers',
            field=models.ManyToManyField(blank=True, related_name='scene_viewers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='device',
            name='name',
            field=models.CharField(max_length=200, unique=True, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$', 'Only alphanumeric, underscore, hyphen, in namespace/idname format allowed.')]),
        ),
        migrations.AlterField(
            model_name='scene',
            name='editors',
            field=models.ManyToManyField(blank=True, related_name='scene_editors', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='scene',
            name='name',
            field=models.CharField(max_length=200, unique=True, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$', 'Only alphanumeric, underscore, hyphen, in namespace/idname format allowed.')]),
        ),
        migrations.CreateModel(
            name='Namespace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9_-]*$', 'Only alphanumeric, underscore, hyphen allowed.')])),
                ('editors', models.ManyToManyField(blank=True, related_name='namespace_editors', to=settings.AUTH_USER_MODEL)),
                ('owners', models.ManyToManyField(blank=True, related_name='namespace_owners', to=settings.AUTH_USER_MODEL)),
                ('viewers', models.ManyToManyField(blank=True, related_name='namespace_viewers', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
