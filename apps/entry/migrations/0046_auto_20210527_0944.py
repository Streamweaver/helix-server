# Generated by Django 3.0.5 on 2021-05-27 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0045_auto_20210521_1130'),
    ]

    operations = [
        migrations.AddField(
            model_name='disaggregatedagecategory',
            name='age_group_from',
            field=models.IntegerField(null=True, verbose_name='Age Group From'),
        ),
        migrations.AddField(
            model_name='disaggregatedagecategory',
            name='age_group_to',
            field=models.IntegerField(null=True, verbose_name='Age Group To'),
        ),
    ]
