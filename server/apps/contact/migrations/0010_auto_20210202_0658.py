# Generated by Django 3.0.5 on 2021-02-02 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0009_merge_20210202_0612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='phone',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='Phone'),
        ),
    ]