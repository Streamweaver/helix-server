# Generated by Django 3.0.5 on 2020-12-17 05:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('event', '0005_auto_20201118_0445'),
    ]

    operations = [
        migrations.AddField(
            model_name='actor',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At'),
        ),
        migrations.AddField(
            model_name='actor',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_actor', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='actor',
            name='last_modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By'),
        ),
        migrations.AddField(
            model_name='actor',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Modified At'),
        ),
        migrations.AddField(
            model_name='actor',
            name='version_id',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Version'),
        ),
    ]
