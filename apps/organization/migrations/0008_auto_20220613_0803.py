# Generated by Django 3.0.5 on 2022-06-13 08:03

import apps.organization.models
from django.db import migrations
import django_enumfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0007_auto_20210623_0357'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='breakdown',
        ),
        migrations.AddField(
            model_name='organizationkind',
            name='reliability',
            field=django_enumfield.db.fields.EnumField(default=0, enum=apps.organization.models.OrganizationKind.ORGANIZATION_RELIABILITY),
        ),
    ]