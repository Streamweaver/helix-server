from django.db import models
from django.db.models import (
    Count,
    Subquery,
    OuterRef,
    IntegerField,
)
from promise import Promise
from promise.dataloader import DataLoader

from apps.entry.models import Figure, FigureCategory, EntryReviewer
from apps.event.models import Event


def batch_load_fn_by_category(keys, category):
    qs = Figure.objects.select_related(
        'entry__event'
    ).filter(
        entry__event__in=keys
    ).order_by().values(
        'entry__event'
    ).annotate(
        total_category_figures=models.Sum(
            'total_figures',
            filter=models.Q(
                role=Figure.ROLE.RECOMMENDED,
                category=category,
            ),
        )
    ).values('entry__event', 'total_category_figures')

    batch_load = {
        item['entry__event']: item['total_category_figures']
        for item in qs
    }

    return Promise.resolve([
        batch_load.get(key) for key in keys
    ])


class TotalIDPFigureByEventLoader(DataLoader):
    def batch_load_fn(self, keys):
        return batch_load_fn_by_category(
            keys,
            FigureCategory.stock_idp_id(),
        )


class TotalNDFigureByEventLoader(DataLoader):
    def batch_load_fn(self, keys):
        return batch_load_fn_by_category(
            keys,
            FigureCategory.flow_new_displacement_id(),
        )


def _if_has_higher_than(status):
    # sets null if there is no status higher than given
    return Subquery(
        EntryReviewer.objects.filter(
            entry=OuterRef('entry'),
            status__gt=status
        ).order_by().values('entry').annotate(c=Count('id')).values('c'),
        output_field=IntegerField()
    )


class EventReviewCountLoader(DataLoader):
    def batch_load_fn(self, keys: list):
        '''
        keys: [entryId]
        '''
        qs = Event.objects.filter(
            id__in=keys
        ).annotate(
            under_review_count=Subquery(
                EntryReviewer.objects.filter(
                    entry__event=OuterRef('pk'),
                    status=EntryReviewer.REVIEW_STATUS.UNDER_REVIEW
                ).annotate(
                    skip=_if_has_higher_than(
                        EntryReviewer.REVIEW_STATUS.UNDER_REVIEW
                    )
                ).exclude(
                    skip__isnull=False
                ).order_by().values('entry__event').annotate(c=Count('entry', distinct=True)).values('c'),
                output_field=IntegerField()
            ),
            signed_off_count=Subquery(
                EntryReviewer.objects.filter(
                    entry__event=OuterRef('pk'),
                    status=EntryReviewer.REVIEW_STATUS.SIGNED_OFF
                ).order_by().values('entry__event').annotate(c=Count('entry', distinct=True)).values('c'),
                output_field=IntegerField()
            ),
            review_complete_count=Subquery(
                EntryReviewer.objects.filter(
                    entry__event=OuterRef('pk'),
                    status=EntryReviewer.REVIEW_STATUS.REVIEW_COMPLETED
                ).annotate(
                    skip=_if_has_higher_than(
                        EntryReviewer.REVIEW_STATUS.REVIEW_COMPLETED
                    )
                ).exclude(
                    skip__isnull=False
                ).order_by().values('entry__event').annotate(c=Count('entry', distinct=True)).values('c'),
                output_field=IntegerField()
            ),
            to_be_reviewed_count=Subquery(
                EntryReviewer.objects.filter(
                    entry__event=OuterRef('pk'),
                    status=EntryReviewer.REVIEW_STATUS.TO_BE_REVIEWED
                ).annotate(
                    skip=_if_has_higher_than(
                        EntryReviewer.REVIEW_STATUS.TO_BE_REVIEWED
                    )
                ).exclude(
                    skip__isnull=False
                ).order_by().values('entry__event').annotate(c=Count('entry', distinct=True)).values('c'),
                output_field=IntegerField()
            ),
        ).values(
            'id', 'under_review_count', 'signed_off_count',
            'review_complete_count', 'to_be_reviewed_count',
        )

        list_to_dict = {
            item['id']: {
                'under_review_count': item['under_review_count'],
                'signed_off_count': item['signed_off_count'],
                'review_complete_count': item['review_complete_count'],
                'to_be_reviewed_count': item['to_be_reviewed_count'],
            }
            for item in qs
        }

        return Promise.resolve([
            list_to_dict.get(event_id, dict())
            for event_id in keys
        ])
