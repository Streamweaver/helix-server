from utils.tests import HelixTestCase
from utils.factories import (
    CountryFactory,
    CountryRegionFactory,
    CrisisFactory,
    EventFactory,
    EntryFactory,
    TagFactory,
    FigureCategoryFactory,
    FigureFactory,
)
from apps.extraction.filters import EntryExtractionFilterSet as f


class TestExtractionFilter(HelixTestCase):
    def setUp(self) -> None:
        self.reg1 = CountryRegionFactory.create()
        self.reg2 = CountryRegionFactory.create()
        self.reg3 = CountryRegionFactory.create()
        self.fig_cat1 = FigureCategoryFactory.create()
        self.fig_cat2 = FigureCategoryFactory.create()
        self.fig_cat3 = FigureCategoryFactory.create()
        self.country1reg1 = CountryFactory.create(region=self.reg1)
        self.country2reg2 = CountryFactory.create(region=self.reg2)
        self.country3reg3 = CountryFactory.create(region=self.reg3)
        self.crisis1 = CrisisFactory.create()
        self.crisis1.countries.set([self.country1reg1, self.country2reg2])
        self.crisis2 = CrisisFactory.create()
        self.crisis2.countries.set([self.country3reg3, self.country2reg2])

        self.event1crisis1 = EventFactory.create(crisis=self.crisis1)
        self.event1crisis1.countries.set([self.country2reg2])
        self.event2crisis1 = EventFactory.create(crisis=self.crisis1)
        self.event2crisis1.countries.set([self.country1reg1])
        self.event3crisis2 = EventFactory.create(crisis=self.crisis2)
        self.event3crisis2.countries.set([self.country2reg2, self.country3reg3])

        self.tag1 = TagFactory.create()
        self.tag2 = TagFactory.create()
        self.tag3 = TagFactory.create()
        self.entry1ev1 = EntryFactory.create(event=self.event1crisis1)
        self.entry1ev1.tags.set([self.tag1, self.tag2])
        self.entry2ev1 = EntryFactory.create(event=self.event1crisis1)
        self.entry2ev1.tags.set([self.tag3])
        self.entry3ev2 = EntryFactory.create(event=self.event2crisis1)
        self.entry3ev2.tags.set([self.tag2])
        self.mid_sep = '2020-09-15'
        self.end_sep = '2020-09-29'
        self.mid_oct = '2020-10-15'
        self.end_oct = '2020-10-29'
        self.mid_nov = '2020-11-16'
        self.end_nov = '2020-11-29'
        self.fig1cat1entry1 = FigureFactory.create(entry=self.entry1ev1, category=self.fig_cat1,
                                                   start_date=self.mid_oct, end_date=self.end_oct)
        self.fig2cat2entry1 = FigureFactory.create(entry=self.entry1ev1, category=self.fig_cat2,
                                                   start_date=self.end_oct, end_date=self.end_nov)
        self.fig3cat2entry2 = FigureFactory.create(entry=self.entry2ev1, category=self.fig_cat2,
                                                   start_date=self.mid_sep, end_date=self.end_oct)
        self.fig4cat1entry3 = FigureFactory.create(entry=self.entry3ev2, category=self.fig_cat1,
                                                   start_date=self.mid_nov, end_date=None)
        self.fig5cat3entry3 = FigureFactory.create(entry=self.entry3ev2, category=self.fig_cat3,
                                                   start_date=self.mid_nov, end_date=self.end_nov)

    def test_filter_by_region(self):
        regions = [self.reg1.id]
        fqs = f(data=dict(event_regions=regions)).qs
        self.assertEqual(set(fqs), {self.entry3ev2})

    def test_filter_by_country(self):
        data = dict(
            event_countries=[self.country2reg2.id]
        )
        fqs = f(data=data).qs
        self.assertEqual(set(fqs), {self.entry1ev1, self.entry2ev1})

        data = dict(
            event_countries=[self.country3reg3.id]
        )
        fqs = f(data=data).qs
        self.assertEqual(set(fqs), set())

    def test_filter_by_crises(self):
        data = dict(
            event_crises=[self.crisis1.id]
        )
        fqs = f(data=data).qs
        self.assertEqual(set(fqs), {self.entry1ev1, self.entry2ev1, self.entry3ev2})

        data['event_crises'] = [self.crisis2.id]
        fqs = f(data=data).qs
        self.assertEqual(set(fqs), set())

    def test_filter_by_categories(self):
        data = dict(
            figure_categories=[self.fig_cat2.id]
        )
        fqs = f(data=data).qs
        self.assertEqual(set(fqs), {self.entry1ev1, self.entry2ev1})
        data = dict(
            figure_categories=[self.fig_cat1.id, self.fig_cat3.id]
        )
        fqs = f(data=data).qs
        self.assertEqual(set(fqs), {self.entry1ev1, self.entry3ev2})

    def test_filter_by_time_frame(self):
        data = dict(
            figure_start_after=self.mid_oct
        )
        eqs = {self.entry1ev1, self.entry3ev2}
        fqs = f(data=data).qs
        self.assertEqual(set(fqs), eqs)

        data['figure_end_before'] = self.mid_nov
        eqs = {self.entry1ev1}
        fqs = f(data=data).qs
        self.assertEqual(set(fqs), eqs)
