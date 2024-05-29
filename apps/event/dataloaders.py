from collections import defaultdict
from django.db import models
from django.db.models import Case, F, When, CharField
from django.contrib.postgres.aggregates import ArrayAgg

from promise import Promise
from promise.dataloader import DataLoader

from apps.entry.models import Figure
from apps.event.models import Event, EventCode


def batch_load_fn_by_category(keys, category):
    """
    Retrieves the total figure for each key in the batch, based on the given category.

    Parameters:
    - keys (list): A list of keys representing the event IDs.
    - category (str): The category for the figures. Should be one of the categories defined in Figure.FIGURE_CATEGORY_TYPES.

    Returns:
    - Promise: A Promise object resolved with a list of total figures corresponding to the keys in the input list.

    Example usage:
    batch_load_fn_by_category(['1', '2', '3'], Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT.value)

    Note:
    - This method assumes the existence of the Event model and the Figure model, both defined elsewhere in the codebase.
    """
    qs = Event.objects.filter(
        id__in=keys
    ).annotate(
        **Event._total_figure_disaggregation_subquery()
    )

    if category == Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT.value:
        qs = qs.annotate(_total=models.F(Event.ND_FIGURES_ANNOTATE))
    else:
        qs = qs.annotate(_total=models.F(Event.IDP_FIGURES_ANNOTATE))

    batch_load = {
        item['id']: item['_total']
        for item in qs.values('id', '_total')
    }

    return Promise.resolve([
        batch_load.get(key) for key in keys
    ])


class TotalIDPFigureByEventLoader(DataLoader):
    """
    Loads the total IDP figure by event for the given keys.

    :param keys: A list of keys to load the total IDP figure for each event.
    :type keys: list

    :return: A dictionary containing the loaded total IDP figure for each event.
    :rtype: dict
    """
    def batch_load_fn(self, keys):
        return batch_load_fn_by_category(
            keys,
            Figure.FIGURE_CATEGORY_TYPES.IDPS.value,
        )


class TotalNDFigureByEventLoader(DataLoader):
    """

    """
    def batch_load_fn(self, keys):
        return batch_load_fn_by_category(
            keys,
            Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT.value,
        )


class MaxStockIDPFigureEndDateByEventLoader(DataLoader):
    """
    A DataLoader class that loads the maximum stock IDP figure end date for a given list of event IDs.

    Methods:
    - batch_load_fn(keys: List[str]) -> Promise[List[Optional[datetime]]]:
        - This method takes in a list of event IDs and returns a Promise that resolves to a list of maximum stock IDP figure end dates corresponding to the given event IDs.
        - It retrieves the events from the database using the given event IDs and annotates each event with the total figure disaggregation subquery.
        - It then extracts the maximum stock IDP figure end date for each event and stores it in a dictionary.
        - Finally, it returns a list of maximum stock IDP figure end dates in the same order as the given event IDs.

    Dependencies:
    - DataLoader: A base class that provides a mechanism for batching and caching data loading operations.

    Usage:
    - Create an instance of MaxStockIDPFigureEndDateByEventLoader.
    - Call the batch_load_fn method, passing in a list of event IDs.
    - Use the resolved Promise to access the maximum stock IDP figure end dates for the corresponding event IDs.
    """
    def batch_load_fn(self, keys):
        qs = Event.objects.filter(
            id__in=keys
        ).annotate(
            **Event._total_figure_disaggregation_subquery()
        )
        batch_load = {
            item['id']: item[Event.IDP_FIGURES_REFERENCE_DATE_ANNOTATE]
            for item in qs.values('id', Event.IDP_FIGURES_REFERENCE_DATE_ANNOTATE)
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class EventEntryCountLoader(DataLoader):
    """
    Class: EventEntryCountLoader

    A class that extends the DataLoader class and provides a method for loading the entry count for a given list of event IDs.

    Attributes:
    - None

    Methods:
    - batch_load_fn(keys): Returns a promise that resolves to a list of entry counts corresponding to the provided event IDs.

        Parameters:
        - keys (list): A list of event IDs for which the entry count needs to be loaded.

        Returns:
        - Promise: Returns a promise that resolves to a list of entry counts corresponding to the provided event IDs.
    """
    def batch_load_fn(self, keys):
        qs = Event.objects.filter(
            id__in=keys
        ).annotate(
            entry_count=models.Subquery(
                Figure.objects.filter(
                    event=models.OuterRef('pk')
                ).order_by().values('event').annotate(
                    count=models.Count('entry', distinct=True)
                ).values('count')[:1],
                output_field=models.IntegerField()
            )
        )
        batch_load = {
            item['id']: item['entry_count']
            for item in qs.values('id', 'entry_count')
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class EventTypologyLoader(DataLoader):
    """

    Class: EventTypologyLoader(DataLoader)
        A DataLoader class responsible for loading event typology data.

    Attributes:
        None

    Methods:
        batch_load_fn(keys: list) -> Promise
            A method that takes a list of keys and loads the corresponding event typology data.

    """
    def batch_load_fn(self, keys: list):
        qs = Event.objects.filter(
            id__in=keys
        ).annotate(
            event_typology=Case(
                When(other_sub_type__isnull=False, then=F('other_sub_type__name')),
                When(violence_sub_type__isnull=False, then=F('violence_sub_type__name')),
                When(disaster_sub_type__isnull=False, then=F('disaster_sub_type__name')),
                output_field=CharField(),
            )
        ).values('id', 'event_typology')
        batch_load = {
            item['id']: item['event_typology']
            for item in qs
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class EventFigureTypologyLoader(DataLoader):
    """
    Class: EventFigureTypologyLoader

    EventFigureTypologyLoader is a class that inherits from the DataLoader class. It provides a method, batch_load_fn, for batch loading event typologies for a given list of event IDs.

    Methods:
    - batch_load_fn(keys: list) -> Promise:
        This method takes a list of event IDs as input and returns a Promise object that resolves to a list of event typologies corresponding to the given event IDs.

        Parameters:
        - keys: list - A list of event IDs.

        Returns:
        - Promise - A Promise object that resolves to a list of event typologies.

    """
    def batch_load_fn(self, keys: list):
        qs = Figure.objects.filter(
            event_id__in=keys
        ).values(
            'event_id'
        ).annotate(
            event_typology=ArrayAgg(Case(
                When(other_sub_type__isnull=False, then=F('other_sub_type__name')),
                When(violence_sub_type__isnull=False, then=F('violence_sub_type__name')),
                When(disaster_sub_type__isnull=False, then=F('disaster_sub_type__name')),
                output_field=CharField(),
            ), distinct=True)
        )
        batch_load = {
            item['event_id']: item['event_typology']
            for item in qs
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class EventReviewCountLoader(DataLoader):
    """

    class EventReviewCountLoader(DataLoader):

        This class is responsible for loading event review counts using a batch load function.

        Attributes:
            None

        Methods:
            batch_load_fn(keys: list) -> Promise:
                Performs a batch load of event review counts.

        """
    def batch_load_fn(self, keys: list):
        qs = Event.objects.filter(
            id__in=keys
        ).annotate(
            **Event.annotate_review_figures_count()
        ).values(
            'id',
            'review_not_started_count',
            'review_in_progress_count',
            'review_re_request_count',
            'review_approved_count',
            'total_count',
            'progress',
        )
        batch_load = {
            item['id']: {
                'review_not_started_count': item['review_not_started_count'],
                'review_in_progress_count': item['review_in_progress_count'],
                'review_re_request_count': item['review_re_request_count'],
                'review_approved_count': item['review_approved_count'],
                'total_count': item['total_count'],
                'progress': item['progress'],
            } for item in qs
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class EventCodeLoader(DataLoader):
    """
    Class EventCodeLoader

    Subclass of DataLoader.

    Methods:
    - batch_load_fn(keys: list) -> Promise

    """
    def batch_load_fn(self, keys: list):
        qs = EventCode.objects.filter(event__id__in=keys)
        _map = defaultdict(list)
        for event_code in qs.all():
            _map[event_code.event_id].append(event_code)
        return Promise.resolve([_map.get(key) for key in keys])


class EventCrisisLoader(DataLoader):
    """
    Load the crisis associated with a list of event IDs.

    This class extends the DataLoader class.

    Methods:
        batch_load_fn(keys: list) -> Promise[List[Optional[Crisis]]]
            - Load the crisis associated with a list of event IDs.

            Parameters:
                keys (list): A list of event IDs.

            Returns:
                Promise[List[Optional[Crisis]]]: A Promise resolving to a list of crisis objects associated with the given event IDs.
    """
    def batch_load_fn(self, keys: list):
        qs = Event.objects.filter(id__in=keys).select_related('crisis').only('id', 'crisis')
        _map = {}
        for event in qs.all():
            _map[event.id] = event.crisis
        return Promise.resolve([_map.get(key) for key in keys])
