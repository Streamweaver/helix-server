# Generated by Django 3.0.14 on 2023-03-22 08:04

from django.db import migrations


class Migration(migrations.Migration):

    def regenerate_event_and_figures_hazards_and_violences(apps, schema_editor):
        from django.db.models import Subquery, OuterRef, Q
        Figure = apps.get_model('entry', 'Figure')
        Event = apps.get_model('event', 'Event')

        # Regenerate event and figure disaster type
        Event.objects.filter(
            Q(disaster_sub_type__isnull=False)
        ).update(
            disaster_type=Subquery(Event.objects.filter(pk=OuterRef('pk')).values('disaster_sub_type__type')[:1]),
        )
        Figure.objects.filter(
            Q(disaster_sub_type__isnull=False)
        ).update(
            disaster_type=Subquery(Figure.objects.filter(pk=OuterRef('pk')).values('disaster_sub_type__type')[:1]),
        )

        # Regenerate event and figure disaster sub category
        Event.objects.filter(
            Q(disaster_type__isnull=False)
        ).update(
            disaster_sub_category=Subquery(Event.objects.filter(pk=OuterRef('pk')).values('disaster_type__disaster_sub_category')[:1]),
        )
        Figure.objects.filter(
            Q(disaster_type__isnull=False)
        ).update(
            disaster_sub_category=Subquery(Figure.objects.filter(pk=OuterRef('pk')).values('disaster_type__disaster_sub_category')[:1]),
        )

        # Regenerate event and figure disaster category
        Event.objects.filter(
            Q(disaster_sub_category__isnull=False)
        ).update(
            disaster_category=Subquery(Event.objects.filter(pk=OuterRef('pk')).values('disaster_sub_category__category')[:1]),
        )
        Figure.objects.filter(
            Q(disaster_sub_category__isnull=False)
        ).update(
            disaster_category=Subquery(Figure.objects.filter(pk=OuterRef('pk')).values('disaster_sub_category__category')[:1]),
        )

        # Regenerate figure and event violence from violence sub type
        Figure.objects.filter(
            violence_sub_type__isnull=False
        ).update(
            violence=Subquery(
                Figure.objects.filter(pk=OuterRef('pk')).values('violence_sub_type__violence')[:1]
            )
        )
        Event.objects.filter(
            violence_sub_type__isnull=False
        ).update(
            violence=Subquery(
                Event.objects.filter(pk=OuterRef('pk')).values('violence_sub_type__violence')[:1]
            )
        )

    dependencies = [
        ('entry', '0082_update_figures_year_data_2023_03_21'),
        ('event', '0031_fix_drought_and_cold_wave_data_migration'),
    ]

    operations = [
        migrations.RunPython(regenerate_event_and_figures_hazards_and_violences, reverse_code=migrations.RunPython.noop),
    ]
