# Generated by Django 3.0.5 on 2021-09-28 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('review', '0005_review_geo_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='age_id',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='Age Id'),
        ),
        migrations.AlterField(
            model_name='review',
            name='strata_id',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='Strata Id'),
        ),
    ]