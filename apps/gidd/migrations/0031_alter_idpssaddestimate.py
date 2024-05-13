# Generated by Django 3.2 on 2024-04-26 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gidd', '0030_auto_20240114_1147'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='fifteen_to_seventeen',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='fifteen_to_twentyfour',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='five_to_elaven',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='five_to_fourteen',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='sixty_five_plus',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='twelve_to_fourteen',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='twelve_to_sixteen',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='twenty_five_to_sixty_four',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='zero_to_forteen',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='zero_to_one',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='zero_to_sventeen',
        ),
        migrations.RemoveField(
            model_name='idpssaddestimate',
            name='zero_to_twenty_four',
        ),
        migrations.AddField(
            model_name='idpssaddestimate',
            name='eighteen_to_fiftynine',
            field=models.IntegerField(null=True, verbose_name='18-59'),
        ),
        migrations.AddField(
            model_name='idpssaddestimate',
            name='five_to_eleven',
            field=models.IntegerField(null=True, verbose_name='5-11'),
        ),
        migrations.AddField(
            model_name='idpssaddestimate',
            name='sixty_plus',
            field=models.IntegerField(null=True, verbose_name='60+'),
        ),
        migrations.AddField(
            model_name='idpssaddestimate',
            name='twelve_to_seventeen',
            field=models.IntegerField(null=True, verbose_name='12-17'),
        ),
        migrations.AlterField(
            model_name='idpssaddestimate',
            name='sex',
            field=models.CharField(max_length=256, verbose_name='Sex'),
        ),
    ]