# Generated by Django 3.2 on 2024-03-26 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0004_auto_20220629_0805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='resourcegroup',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
    ]
