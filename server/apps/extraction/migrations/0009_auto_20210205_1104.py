# Generated by Django 3.0.5 on 2021-02-05 11:04

import apps.crisis.models
from django.db import migrations
import django_enumfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('extraction', '0008_auto_20210205_1028'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extractionquery',
            name='event_crisis_type',
            field=django_enumfield.db.fields.EnumField(blank=True, enum=apps.crisis.models.Crisis.CRISIS_TYPE, null=True),
        ),
    ]
