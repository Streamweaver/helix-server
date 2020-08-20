# Generated by Django 3.0.5 on 2020-08-18 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('country', '0001_initial'),
        ('contact', '0003_auto_20200817_0533'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='countries_of_operation',
            field=models.ManyToManyField(blank=True, help_text='In which countries does this contact person operate?', related_name='operating_contacts', to='country.Country'),
        ),
    ]
