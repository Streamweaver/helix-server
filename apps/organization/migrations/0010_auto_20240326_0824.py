# Generated by Django 3.2 on 2024-03-26 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0009_auto_20220803_0816'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='organizationkind',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
    ]
