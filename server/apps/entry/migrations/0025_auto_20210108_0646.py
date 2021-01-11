# Generated by Django 3.0.5 on 2021-01-08 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0006_auto_20201231_0707'),
        ('entry', '0024_merge_20210104_0911'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entry',
            name='publisher',
        ),
        migrations.RemoveField(
            model_name='entry',
            name='source',
        ),
        migrations.AddField(
            model_name='entry',
            name='publishers',
            field=models.ManyToManyField(blank=True, related_name='published_entries', to='organization.Organization', verbose_name='Publisher'),
        ),
        migrations.AddField(
            model_name='entry',
            name='sources',
            field=models.ManyToManyField(blank=True, related_name='sourced_entries', to='organization.Organization', verbose_name='Source'),
        ),
    ]
