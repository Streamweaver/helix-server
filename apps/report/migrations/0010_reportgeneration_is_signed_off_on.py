# Generated by Django 3.0.5 on 2021-03-10 04:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report', '0009_auto_20210305_1918'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportgeneration',
            name='is_signed_off_on',
            field=models.DateTimeField(null=True, verbose_name='Is signed off on'),
        ),
    ]