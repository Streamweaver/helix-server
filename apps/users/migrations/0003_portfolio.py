# Generated by Django 3.0.5 on 2021-06-06 17:38

import apps.users.enums
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_enumfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('country', '0013_auto_20210604_0534'),
        ('users', '0002_user_full_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Portfolio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', django_enumfield.db.fields.EnumField(enum=apps.users.enums.USER_ROLE)),
                ('monitoring_sub_region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='portfolios', to='country.MonitoringSubRegion', verbose_name='Monitoring Sub-region')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolios', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'unique_together': {('user', 'role', 'monitoring_sub_region')},
            },
        ),
    ]
