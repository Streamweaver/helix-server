# Generated by Django 3.0.5 on 2021-09-21 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extraction', '0015_extractionquery_filter_figure_category_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='extractionquery',
            name='filter_entry_has_review_comments',
            field=models.NullBooleanField(default=None, verbose_name='Has review comments'),
        ),
    ]
