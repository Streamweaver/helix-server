# Generated by Django 3.2 on 2023-04-25 04:41

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gidd', '0005_releasemetadata'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='GiddLog',
            new_name='StatusLog',
        ),
    ]
