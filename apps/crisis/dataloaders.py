from django.db import models
from promise import Promise
from promise.dataloader import DataLoader

from apps.entry.models import Figure
from apps.crisis.models import Crisis
from apps.event.models import Event


def batch_load_fn_by_category(keys, category):
    """
    Load batch figures by category.

    :param keys: List of Crisis object IDs.
    :type keys: list
    :param category: Category of figures to load.
    :type category: str
    :return: List of batch figures for each key in keys.
    :rtype: list
    """
    qs = Crisis.objects.filter(
        id__in=keys
    ).annotate(
        **Crisis._total_figure_disaggregation_subquery()
    )

    if category == Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT:
        qs = qs.annotate(_total=models.F(Crisis.ND_FIGURES_ANNOTATE))
    else:
        qs = qs.annotate(_total=models.F(Crisis.IDP_FIGURES_ANNOTATE))

    batch_load = {
        item['id']: item['_total']
        for item in qs.values('id', '_total')
    }

    return Promise.resolve([
        batch_load.get(key) for key in keys
    ])


class TotalIDPFigureByCrisisLoader(DataLoader):
    """
    Class TotalIDPFigureByCrisisLoader

    This class is a DataLoader that is used to load total figures of IDP (Internally Displaced Persons) by crisis. It
    inherits from the DataLoader class.

    Methods:
    - batch_load_fn(keys): This method takes a list of keys and returns the batch load function for loading total IDP
    figures by crisis.

    """
    def batch_load_fn(self, keys):
        return batch_load_fn_by_category(
            keys,
            Figure.FIGURE_CATEGORY_TYPES.IDPS.value,
        )


class TotalNDFigureByCrisisLoader(DataLoader):
    """
    Class TotalNDFigureByCrisisLoader

    This class extends the DataLoader class and provides a batch_load_fn method specific to loading total figures for
    new displacement crises.

    Attributes:
        None

    Methods:
        - batch_load_fn(keys):
            This method retrieves data for the given keys, where each key represents a particular crisis. It calls the
            batch_load_fn_by_category function from Figure module to load figures specifically related to new
            displacement crises. The loaded figures are then returned.

    """
    def batch_load_fn(self, keys):
        return batch_load_fn_by_category(
            keys,
            Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT.value,
        )


class MaxStockIDPFigureEndDateByCrisisLoader(DataLoader):
    """
    Class: MaxStockIDPFigureEndDateByCrisisLoader

    This class is a DataLoader class that loads the maximum stock IDP figure end date by crisis.

    Methods:
    - batch_load_fn(keys): This method takes a list of keys and returns a Promise that resolves to a list of maximum
    stock IDP figure end dates for the given keys. It retrieves the data from the Crisis model by filtering with the
    keys and annotates each crisis object with the total figure disaggregation subquery. It then creates a dictionary,
    batch_load, where the key is the crisis id and the value is the IDP figures reference date. Finally, it returns a
    list of IDP figure end dates corresponding to the given keys.

    Note: This class inherits from the DataLoader class and overrides the batch_load_fn method.
    """
    def batch_load_fn(self, keys):
        qs = Crisis.objects.filter(
            id__in=keys
        ).annotate(
            **Crisis._total_figure_disaggregation_subquery()
        )
        batch_load = {
            item['id']: item[Event.IDP_FIGURES_REFERENCE_DATE_ANNOTATE]
            for item in qs.values('id', Event.IDP_FIGURES_REFERENCE_DATE_ANNOTATE)
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class EventCountLoader(DataLoader):
    """
    A DataLoader class for loading event count data for Crisis objects.

    Usage:
        event_loader = EventCountLoader()
        event_loader.batch_load_fn(keys)

    Methods:
        batch_load_fn(keys)
            Loads event count data for the given keys.

            Parameters:
                keys (list): A list of keys representing Crisis objects.

            Returns:
                Promise: A Promise object containing the event count data for the keys.
    """
    def batch_load_fn(self, keys):
        qs = Crisis.objects.filter(
            id__in=keys
        ).annotate(
            event_count=models.Subquery(
                Event.objects.filter(
                    crisis=models.OuterRef('pk')
                ).order_by().values('crisis').annotate(
                    count=models.Count('crisis')
                ).values('count')[:1],
                output_field=models.IntegerField()
            )
        )
        batch_load = {
            item['id']: item['event_count']
            for item in qs.values('id', 'event_count')
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class CrisisReviewCountLoader(DataLoader):
    """
    Class: CrisisReviewCountLoader

    The CrisisReviewCountLoader class is a DataLoader subclass that is responsible for loading crisis review count data
    for a given list of keys.

    Methods:
    - batch_load_fn(keys: list): This method loads the crisis review count data for the specified list of keys. It uses
    the Crisis model to query the database and fetch the required data. The method returns a Promise object that
    resolves to a list of batch-loaded data.

    Attributes:

    - None

    """
    def batch_load_fn(self, keys: list):
        qs = Crisis.objects.filter(
            id__in=keys
        ).annotate(
            **Crisis.annotate_review_figures_count()
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
