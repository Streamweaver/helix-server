# Generated by Django 3.2 on 2024-04-29 08:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('country', '0018_auto_20240326_0824'),
    ]

    operations = [
        migrations.AddField(
            model_name='householdsize',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Created At'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='householdsize',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_householdsize', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='householdsize',
            name='data_source_category',
            field=models.CharField(default='', max_length=255, verbose_name='Data Source Category'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='householdsize',
            name='is_active',
            field=models.BooleanField(default=False, verbose_name='Is active?'),
        ),
        migrations.AddField(
            model_name='householdsize',
            name='last_modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By'),
        ),
        migrations.AddField(
            model_name='householdsize',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Modified At'),
        ),
        migrations.AddField(
            model_name='householdsize',
            name='notes',
            field=models.TextField(blank=True, null=True, verbose_name='Notes'),
        ),
        migrations.AddField(
            model_name='householdsize',
            name='source',
            field=models.CharField(default='', max_length=255, verbose_name='Source'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='householdsize',
            name='source_link',
            field=models.CharField(default='', max_length=255, verbose_name='Source Link'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='householdsize',
            name='version_id',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Version'),
        ),
        migrations.AlterUniqueTogether(
            name='householdsize',
            unique_together=set(),
        ),
    ]
