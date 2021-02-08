# Generated by Django 3.0.5 on 2021-02-04 10:41

import apps.crisis.models
from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_enumfield.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organization', '0006_auto_20201231_0707'),
        ('entry', '0033_auto_20210204_0735'),
        ('contrib', '0005_sourcepreview'),
        ('country', '0009_auto_20210204_0458'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContextualUpdate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_id', models.CharField(blank=True, max_length=32, null=True, verbose_name='Old primary key')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created At')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified At')),
                ('version_id', models.CharField(blank=True, max_length=16, null=True, verbose_name='Version')),
                ('url', models.URLField(blank=True, max_length=2000, null=True, verbose_name='Source URL')),
                ('article_title', models.TextField(verbose_name='Article Title')),
                ('publish_date', models.DateTimeField(blank=True, null=True, verbose_name='Published DateTime')),
                ('source_excerpt', models.TextField(blank=True, null=True, verbose_name='Excerpt from Source')),
                ('idmc_analysis', models.TextField(null=True, verbose_name='IDMC Analysis')),
                ('is_confidential', models.BooleanField(default=False, verbose_name='Confidential Source')),
                ('crisis_types', django.contrib.postgres.fields.ArrayField(base_field=django_enumfield.db.fields.EnumField(enum=apps.crisis.models.Crisis.CRISIS_TYPE), blank=True, null=True, size=None)),
                ('countries', models.ManyToManyField(blank=True, to='country.Country')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_contextualupdate', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contrib.Attachment', verbose_name='Attachment')),
                ('last_modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
                ('preview', models.OneToOneField(blank=True, help_text='After the preview has been generated pass its idalong during entry creation, so that during entry update the preview can be obtained.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contextual_update', to='contrib.SourcePreview')),
                ('publishers', models.ManyToManyField(blank=True, related_name='published_contextual_updates', to='organization.Organization', verbose_name='Publisher')),
                ('sources', models.ManyToManyField(blank=True, related_name='sourced_contextual_updates', to='organization.Organization', verbose_name='Source')),
                ('tags', models.ManyToManyField(blank=True, to='entry.FigureTag')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]