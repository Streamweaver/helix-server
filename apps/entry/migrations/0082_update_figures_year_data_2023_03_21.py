# Generated by Django 3.0.14 on 2023-03-21 13:48

import csv
from io import StringIO

from django.db import migrations


CSV_DATE = '''
old_id,corrected_start_date,corrected_end_date
62,2016-12-28,2016-12-31
4119,2016-12-24,2016-12-31
4177,2016-01-01,2016-03-17
4179,2016-01-01,2016-05-31
4201,2016-01-01,2016-12-31
4876,2017-01-01,2017-06-15
4908,2016-12-25,2016-12-31
7743,2017-12-24,2017-12-31
7857,2017-01-01,2017-12-31
7873,2017-05-17,2017-12-31
7925,2017-01-01,2017-12-31
8250,2017-11-17,2017-12-31
8283,2017-12-19,2017-12-31
8590,2017-01-01,2017-12-31
8703,2017-01-27,2017-12-31
8801,2017-12-16,2017-12-31
10117,2018-01-01,2018-02-07
12074,2018-01-01,2018-04-30
21110,2018-12-22,2018-12-31
21122,2018-12-18,2018-12-31
21242,2018-12-27,2018-12-31
21245,2018-12-27,2018-12-31
21248,2018-12-27,2018-12-31
21249,2018-12-31,2018-12-31
21285,2018-12-23,2018-12-31
21444,2018-12-26,2018-12-31
21457,2018-12-27,2018-12-31
21533,2018-12-31,2018-12-31
21782,2018-12-03,2018-12-31
21877,2018-01-01,2018-12-31
22136,2018-01-01,2018-12-31
22137,2018-01-01,2018-12-31
22138,2018-01-01,2018-12-31
22299,2018-01-01,2018-12-31
23758,2019-01-01,2019-01-06
24020,2018-01-01,2018-12-31
25801,2019-01-01,2019-06-11
25804,2019-01-01,2019-06-11
25805,2019-01-01,2019-06-11
26426,2019-01-01,2019-03-31
26921,2019-01-01,2019-05-31
33354,2018-01-01,2018-12-31
33355,2018-01-01,2018-12-31
33356,2018-01-01,2018-12-31
36069,2019-12-31,2019-12-31
36085,2019-12-31,2019-12-31
36233,2019-12-27,2019-12-31
36320,2019-12-29,2019-12-31
36702,2019-12-20,2019-12-31
36727,2019-12-20,2019-12-31
36748,2019-12-20,2019-12-31
36765,2019-12-19,2019-12-31
36798,2019-12-21,2019-12-31
36803,2019-12-20,2019-12-31
36866,2019-12-20,2019-12-31
36911,2019-12-28,2019-12-31
37796,2019-01-01,2019-12-31
37797,2019-01-01,2019-12-31
37798,2019-01-01,2019-12-31
37800,2019-01-01,2019-12-31
37801,2019-01-01,2019-12-31
37802,2019-01-01,2019-12-31
37803,2019-01-01,2019-12-31
37804,2019-01-01,2019-12-31
37805,2019-01-01,2019-12-31
37806,2019-01-01,2019-12-31
37807,2019-01-01,2019-12-31
37809,2019-01-01,2019-12-31
37817,2019-01-01,2019-12-31
37821,2019-01-01,2019-12-31
37822,2019-01-01,2019-12-31
37934,2019-10-01,2019-12-31
41276,2020-01-01,2020-02-26
44869,2020-01-01,2020-01-17
46226,2020-01-01,2020-03-23
51214,2019-09-01,2019-12-31
51216,2019-09-01,2019-12-31
51983,2020-01-01,2020-12-31
52501,2020-12-29,2020-12-31
52831,2020-01-01,2020-12-29
53146,2020-01-01,2020-08-30
53768,2020-02-01,2020-12-31
56179,2021-01-01,2021-01-25
57313,2021-01-01,2021-04-08
59283,2020-12-30,2020-12-31
61918,2018-01-01,2018-12-31
61920,2018-01-01,2018-12-31
61923,2018-01-01,2018-12-31
61925,2019-12-30,2019-12-31
62361,2021-12-30,2021-12-31
63051,2021-11-28,2021-12-31
63893,2016-07-11,2016-12-31
66196,2021-01-01,2021-12-31
66202,2021-01-01,2021-12-31
'''


def update_figure_data(apps, schema_editor):
    Figure = apps.get_model('entry', 'Figure')
    reader = csv.DictReader(
        StringIO(CSV_DATE),
        fieldnames=('old_id', 'corrected_start_date', 'corrected_end_date'),
    )
    next(reader)  # Skip header
    for row in reader:
        # NOTE: old_id can have multiple result so doing this one by one for now
        Figure.objects.filter(old_id=row['old_id']).update(
            start_date=row['corrected_start_date'],
            end_date=row['corrected_end_date'],
        )


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0081_fix_total_figures_after_round_half_up'),
    ]

    operations = [
        migrations.RunPython(
            update_figure_data,
            reverse_code=migrations.RunPython.noop
        ),
    ]
