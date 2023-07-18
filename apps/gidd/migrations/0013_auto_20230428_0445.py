# Generated by Django 3.2 on 2023-04-28 04:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0031_fix_drought_and_cold_wave_data_migration'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gidd', '0012_auto_20230425_1017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conflict',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='conflict',
            name='year',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='conflictlegacy',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='conflictlegacy',
            name='year',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='disaster',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='gidd_events', to='event.event', verbose_name='Event'),
        ),
        migrations.AlterField(
            model_name='disaster',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='disaster',
            name='year',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='disasterlegacy',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='disasterlegacy',
            name='year',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='releasemetadata',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='releasemetadata',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='users.user', verbose_name='Modified by'),
        ),
        migrations.AlterField(
            model_name='statuslog',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]