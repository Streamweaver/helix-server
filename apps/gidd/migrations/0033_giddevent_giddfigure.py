# Generated by Django 3.2 on 2024-05-03 08:35

import apps.crisis.models
import apps.entry.models
from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django_enumfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('country', '0019_alter_household_size'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('event', '0001_auto_20240326_0824'),
        ('entry', '0099_alter_externalapidump_api_type'),
        ('gidd', '0032_disaster_displacement_occurred'),
    ]

    operations = [
        migrations.CreateModel(
            name='GiddEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified At')),
                ('version_id', models.CharField(blank=True, max_length=16, null=True, verbose_name='Version')),
                ('name', models.CharField(max_length=256, verbose_name='Event Name')),
                ('cause', django_enumfield.db.fields.EnumField(enum=apps.crisis.models.Crisis.CRISIS_TYPE)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('start_date_accuracy', models.TextField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('end_date_accuracy', models.TextField(blank=True, null=True)),
                ('glide_numbers', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Event Codes'), default=list, size=None)),
                ('event_codes', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Event Codes'), default=list, size=None)),
                ('event_codes_type', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Event Code Types'), default=list, size=None)),
                ('event_codes_iso3', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Event Code ISO3'), default=list, size=None)),
                ('violence_name', models.CharField(blank=True, max_length=256, null=True)),
                ('violence_sub_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('disaster_category_name', models.CharField(blank=True, max_length=256, null=True)),
                ('disaster_sub_category_name', models.CharField(blank=True, max_length=256, null=True)),
                ('disaster_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('disaster_sub_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('other_sub_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('osv_sub_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_giddevent', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('disaster_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.disastercategory', verbose_name='Hazard Category')),
                ('disaster_sub_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.disastersubcategory', verbose_name='Hazard Sub Category')),
                ('disaster_sub_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.disastersubtype', verbose_name='Hazard Sub Type')),
                ('disaster_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.disastertype', verbose_name='Hazard Type')),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.event', verbose_name='Event')),
                ('last_modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
                ('osv_sub_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.osvsubtype', verbose_name='OSV sub type')),
                ('other_sub_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.othersubtype', verbose_name='Other sub type')),
                ('violence', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.violence', verbose_name='Violence')),
                ('violence_sub_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.violencesubtype', verbose_name='Violence Sub Type')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GiddFigure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified At')),
                ('version_id', models.CharField(blank=True, max_length=16, null=True, verbose_name='Version')),
                ('iso3', models.CharField(max_length=5, verbose_name='ISO3')),
                ('country_name', models.CharField(max_length=256, verbose_name='Country name')),
                ('geographical_region_name', models.CharField(blank=True, max_length=256, null=True, verbose_name='Geographical Region')),
                ('term', django_enumfield.db.fields.EnumField(blank=True, enum=apps.entry.models.Figure.FIGURE_TERMS, null=True)),
                ('year', models.IntegerField()),
                ('unit', django_enumfield.db.fields.EnumField(enum=apps.entry.models.Figure.UNIT)),
                ('category', django_enumfield.db.fields.EnumField(blank=True, enum=apps.entry.models.Figure.FIGURE_CATEGORY_TYPES, null=True)),
                ('cause', django_enumfield.db.fields.EnumField(blank=True, enum=apps.crisis.models.Crisis.CRISIS_TYPE, null=True)),
                ('total_figures', models.PositiveIntegerField(verbose_name='Total Figures')),
                ('household_size', models.FloatField(blank=True, null=True, verbose_name='Household Size')),
                ('reported', models.PositiveIntegerField(verbose_name='Reported Figures')),
                ('start_date', models.DateField(blank=True, null=True)),
                ('start_date_accuracy', models.TextField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('end_date_accuracy', models.TextField(blank=True, null=True)),
                ('stock_date', models.DateField(blank=True, null=True)),
                ('stock_date_accuracy', models.TextField(blank=True, null=True)),
                ('stock_reporting_date', models.DateField(blank=True, null=True)),
                ('sources', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Sources'), default=list, size=None)),
                ('sources_type', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Sources Type'), default=list, size=None)),
                ('publishers', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Publishers'), default=list, size=None)),
                ('is_housing_destruction', models.BooleanField(blank=True, default=False, null=True, verbose_name='Is Housing Destruction')),
                ('locations_coordinates', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Location Coordinates'), default=list, size=None)),
                ('locations_names', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Location Names'), default=list, size=None)),
                ('locations_accuracy', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Location Accuracy'), default=list, size=None)),
                ('locations_type', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256, verbose_name='Location Type'), default=list, size=None)),
                ('displacement_occurred', django_enumfield.db.fields.EnumField(blank=True, enum=apps.entry.models.Figure.DISPLACEMENT_OCCURRED, null=True)),
                ('violence_name', models.CharField(blank=True, max_length=256, null=True)),
                ('violence_sub_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('disaster_category_name', models.CharField(blank=True, max_length=256, null=True)),
                ('disaster_sub_category_name', models.CharField(blank=True, max_length=256, null=True)),
                ('disaster_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('disaster_sub_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('other_sub_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('osv_sub_type_name', models.CharField(blank=True, max_length=256, null=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='gidd_figures', to='country.country', verbose_name='Country')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_giddfigure', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('disaster_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.disastercategory', verbose_name='Figure Hazard Category')),
                ('disaster_sub_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.disastersubcategory', verbose_name='Figure Hazard Sub Category')),
                ('disaster_sub_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.disastersubtype', verbose_name='Figure Hazard Sub Type')),
                ('disaster_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.disastertype', verbose_name='Figure Hazard Type')),
                ('figure', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='entry.figure')),
                ('gidd_event', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='gidd_figures', to='gidd.giddevent', verbose_name='GIDD Event')),
                ('last_modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
                ('osv_sub_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.osvsubtype', verbose_name='Figure OSV sub type')),
                ('other_sub_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.othersubtype', verbose_name='Other sub type')),
                ('violence', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.violence', verbose_name='Figure Violence')),
                ('violence_sub_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='event.violencesubtype', verbose_name='Figure Violence Sub Type')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]