# Generated by Django 3.0.5 on 2020-08-12 07:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('designation', models.PositiveSmallIntegerField(choices=[(0, 'Mr'), (1, 'Ms')], verbose_name='Designation')),
                ('name', models.CharField(max_length=256, verbose_name='Title')),
                ('country', models.PositiveIntegerField(default=1, verbose_name='Country')),
                ('job_title', models.CharField(max_length=256, verbose_name='Job Title')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to='organization.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='Communication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country', models.PositiveIntegerField(default=1, verbose_name='Country')),
                ('subject', models.CharField(max_length=512, verbose_name='Subject')),
                ('content', models.TextField(verbose_name='Content')),
                ('date', models.DateField(blank=True, help_text='Date on which communication occurred.', null=True, verbose_name='Date')),
                ('medium', models.PositiveSmallIntegerField(choices=[(0, 'Mail'), (1, 'Phone')], verbose_name='Medium')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='communications', to='contact.Contact')),
            ],
        ),
    ]
