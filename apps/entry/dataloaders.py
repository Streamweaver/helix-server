from django.db import models
from django.contrib.postgres.aggregates.general import StringAgg
from promise import Promise
from promise.dataloader import DataLoader
from django.db.models import Case, F, When, CharField, Q
from collections import defaultdict

from apps.common.utils import EXTERNAL_ARRAY_SEPARATOR
from apps.entry.models import Entry, Figure
from apps.review.models import UnifiedReviewComment


def batch_load_fn_by_category(keys, category):
    """

    Parameters:
    - keys (list): A list of entry keys to load figures for.
    - category (str): The figure category type.

    Returns:
    - Promise: A promise that resolves to a list of"""
    qs = Entry.objects.filter(
        id__in=keys
    ).annotate(
        **Entry._total_figure_disaggregation_subquery()
    )

    if category == Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT:
        qs = qs.annotate(_total=models.F(Entry.ND_FIGURES_ANNOTATE))
    else:
        qs = qs.annotate(_total=models.F(Entry.IDP_FIGURES_ANNOTATE))

    batch_load = {
        item['id']: item['_total']
        for item in qs.values('id', '_total')
    }

    return Promise.resolve([
        batch_load.get(key) for key in keys
    ])


class TotalIDPFigureByEntryLoader(DataLoader):
    """
    class TotalIDPFigureByEntryLoader(DataLoader):
        """
    def batch_load_fn(self, keys):
        return batch_load_fn_by_category(
            keys, Figure.FIGURE_CATEGORY_TYPES.IDPS
        )


class TotalNDFigureByEntryLoader(DataLoader):
    """
    Class TotalNDFigureByEntryLoader

    This class is a DataLoader that loads the total ND figure by entry.

    Attributes:
    - None

    Methods:
    - batch_load_fn(keys): Returns the total ND figure batch loaded by entry.

    """
    def batch_load_fn(self, keys):
        return batch_load_fn_by_category(
            keys, Figure.FIGURE_CATEGORY_TYPES.NEW_DISPLACEMENT
        )


class FigureTypologyLoader(DataLoader):
    """

    class FigureTypologyLoader(DataLoader):
        def batch_load_fn(self, keys: list) -> list:
            """
    def batch_load_fn(self, keys: list):
        qs = Figure.objects.filter(
            id__in=keys
        ).annotate(
            figure_typology=Case(
                When(other_sub_type__isnull=False, then=F('other_sub_type__name')),
                When(violence_sub_type__isnull=False, then=F('violence_sub_type__name')),
                When(disaster_sub_type__isnull=False, then=F('disaster_sub_type__name')),
                output_field=CharField(),
            )
        ).values('id', 'figure_typology')
        batch_load = {
            item['id']: item['figure_typology']
            for item in qs
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class FigureGeoLocationLoader(DataLoader):
    """

    Class: FigureGeoLocationLoader(DataLoader)

    This class is a subclass of DataLoader and is responsible for loading the geo-locations of figures.

    Methods:
    - batch_load_fn(keys)
        - Parameters"""
    def batch_load_fn(self, keys):
        qs = Figure.objects.filter(
            id__in=keys
        ).annotate(
            geolocations=StringAgg('geo_locations__display_name', EXTERNAL_ARRAY_SEPARATOR)
        ).values('id', 'geolocations')
        batch_load = {
            item['id']: item['geolocations']
            for item in qs
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class FigureSourcesReliability(DataLoader):
    """

    Class: FigureSourcesReliability

    This class extends the DataLoader class and provides a method for batch loading the sources reliability of figure
    objects.

    Methods:
    - batch_load_fn(keys): This method loads the sources reliability for a batch of figure objects specified by the"""
    def batch_load_fn(self, keys):
        qs = Figure.objects.filter(
            id__in=keys
        ).annotate(
            **Figure.annotate_sources_reliability()
        ).values('id', 'sources_reliability')
        batch_load = {
            item['id']: item['sources_reliability']
            for item in qs
        }
        return Promise.resolve([
            batch_load.get(key) for key in keys
        ])


class FigureLastReviewCommentStatusLoader(DataLoader):
    """
    class FigureLastReviewCommentStatusLoader(DataLoader):
        A data loader class for retrieving the last review comment status for figures.

        DataLoader Subclass Methods:
            - batch_load_fn(keys):
                Retrieves the last review comment"""
    def batch_load_fn(self, keys):
        review_comment_qs = UnifiedReviewComment.objects.filter(
            Q(figure__in=keys) and
            Q(comment_type__in=[
                UnifiedReviewComment.REVIEW_COMMENT_TYPE.GREEN,
                UnifiedReviewComment.REVIEW_COMMENT_TYPE.RED,
            ])
        ).order_by(
            'figure_id',
            'field',
            '-id',
        ).distinct(
            'figure_id',
            'field',
        ).values(
            'id',
            'figure_id',
            'field',
            'comment_type',
        )
        _map = defaultdict(list)
        for item in review_comment_qs:
            id = item['id']
            field = item['field']
            comment_type = item['comment_type']
            _map[item['figure_id']].append(
                {
                    'id': id,
                    'field': field,
                    'comment_type': comment_type,
                }
            )
        return Promise.resolve([_map[key] for key in keys])


class FigureEntryLoader(DataLoader):
    """
    Class FigureEntryLoader

    This class is a DataLoader subclass used for loading FigureEntry objects based on a list of figure IDs.

    """
    def batch_load_fn(self, keys: list):
        qs = Figure.objects.filter(id__in=keys).select_related('entry').only('id', 'entry')
        _map = {}
        for figure in qs.all():
            _map[figure.id] = figure.entry
        return Promise.resolve([_map.get(key) for key in keys])


class EntryDocumentLoader(DataLoader):
    """
    EntryDocumentLoader extends DataLoader class and is responsible for loading Entry documents based on a list of key
    values.

    Methods:
        - batch_load_fn(keys: list) -> Promise[List[Document]]:
            - This method takes a list of key values"""
    def batch_load_fn(self, keys: list):
        qs = Entry.objects.filter(id__in=keys).select_related('document').only('id', 'document')
        _map = {}
        for entry in qs.all():
            _map[entry.id] = entry.document
        return Promise.resolve([_map.get(key) for key in keys])


class EntryPreviewLoader(DataLoader):
    """

    EntryPreviewLoader

    This class is a DataLoader subclass that is responsible for loading preview data for Entry objects.

    Public Methods:
    - batch_load_fn(keys: list): This method takes in a list of keys and loads the preview data"""
    def batch_load_fn(self, keys: list):
        qs = Entry.objects.filter(id__in=keys).select_related('preview').only('id', 'preview')
        _map = {}
        for entry in qs.all():
            _map[entry.id] = entry.preview
        return Promise.resolve([_map.get(key) for key in keys])
