# Generated by Django 3.2 on 2023-04-29 08:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gidd', '0014_alter_disaster_event'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='statuslog',
            options={'permissions': (('update_gidd_data_gidd', 'Can update GIDD data'),)},
        ),
    ]