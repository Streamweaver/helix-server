# Generated by Django 3.0.5 on 2021-06-14 06:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('country', '0012_auto_20210614_0641'),
    ]

    operations = [
        migrations.AddField(
            model_name='country',
            name='sub_region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='countries', to='country.CountrySubRegion', verbose_name='Sub Region'),
        ),
    ]
