# Generated by Django 3.2 on 2023-05-19 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contrib', '0023_alter_clienttrackinfo_api_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='is_active',
            field=models.BooleanField(default=False, verbose_name='Is active?'),
        ),
    ]
