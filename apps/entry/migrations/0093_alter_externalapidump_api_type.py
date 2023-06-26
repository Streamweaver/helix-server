# Generated by Django 3.2 on 2023-06-22 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0092_alter_externalapidump_api_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalapidump',
            name='api_type',
            field=models.CharField(choices=[('idus', '/external-api/idus/last-180-days/'), ('idus-all', '/external-api/idus/all/'), ('idus-all-disaster', '/external-api/idus/all/disaster/'), ('gidd-country-rest', '/external-api/gidd/countries/'), ('gidd-conflict-rest', '/external-api/gidd/conflicts/'), ('gidd-disaster-rest', '/external-api/gidd/disasters/'), ('gidd-displacement-rest', '/external-api/gidd/displacements/'), ('gidd-disaster-export-rest', '/external-api/gidd/disasters/export/'), ('gidd-displacement-export-rest', '/external-api/gidd/displacements/export/'), ('gidd-public-figure-analysis-rest', '/external-api/gidd/public-figure-analyses/'), ('gidd-conflict-graphql', 'query.giddPublicConflicts'), ('gidd-disaster-graphql', 'query.giddPublicDisasters'), ('gidd-displacement-data-graphql', 'query.giddPublicDisplacements'), ('gidd-public-figure-analysis-graphql', 'query.giddPublicFigureAnalysisList'), ('gidd-conflict-stat-graphql', 'query.giddPublicConflictStatistics'), ('gidd-disaster-stat-graphql', 'query.giddPublicDisasterStatistics'), ('gidd-hazard-type-graphql', 'query.giddPublicHazardTypes'), ('gidd-year-graphql', 'query.giddPublicYear'), ('gidd-event-graphql', 'query.giddPublicEvent'), ('gidd-combined-stat-graphql', 'query.giddPublicCombinedStatistics'), ('gidd-release-meta-data-graphql', 'query.giddPublicReleaseMetaData'), ('gidd-public-countries-graphql', 'query.giddPublicCountries')], max_length=40),
        ),
    ]
