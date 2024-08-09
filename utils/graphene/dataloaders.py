from collections import defaultdict

from promise import Promise
from promise.dataloader import DataLoader
from django.db.models import (
    Prefetch,
    Subquery,
    OuterRef,
    Count,
    IntegerField,
)


def get_relations(model1, model2):
    """
    Retrieve a list of relation fields between two models.

    Args:
        model1 (django.db.models.Model): The first model.
        model2 (django.db.models.Model): The second model.

    Returns:
        list: A list of relation field names between the two models.
    """
    relations = []
    for field in model1._meta.get_fields():
        if field.is_relation and field.related_model == model2:
            relations.append(field.name)
    return relations


def get_related_name(model1, model2):
    """
    Returns the related name between two models.

    Parameters:
    - model1 (str): The name of the first model.
    - model2 (str): The name of the second model.

    Returns:
    str: The related name between the two models.

    """
    relations = get_relations(model1, model2)
    if relations:
        return relations[0]


class DataLoaderException(Exception):
    """

    The DataLoaderException class is a custom exception class that is used to raise exceptions related to data loading
    operations.

    Attributes:
        message (str): The error message associated with the exception.

    """


class CountLoader(DataLoader):
    """

    Class CountLoader

    A DataLoader subclass for loading the count of related objects.

    Methods:
    - load: Loads the count of related objects for the given parent and child models.
    - batch_load_fn: Retrieves the count of related objects for multiple parent keys.

    Attributes:
    - parent: The parent model.
    - child: The child model.
    - related_name: The related name used in the child model to refer to the parent model.
    - reverse_related_name: The related name used in the parent model to refer to the child model.
    - accessor: The accessor used to access the related objects in the parent model.
    - pagination: The pagination configuration.
    - filterset_class: The filterset class to apply to the queryset.
    - filter_kwargs: The filter kwargs to apply to the queryset.
    - request: The request object.
    - kwargs: Additional kwargs passed for pagination.

    """
    def load(
        self,
        key,
        parent,
        child,
        related_name=None,
        reverse_related_name=None,
        accessor=None,
        pagination=None,
        filterset_class=None,
        filter_kwargs=None,
        request=None,
        **kwargs
    ):
        self.parent = parent
        self.child = child
        self.related_name = related_name
        self.reverse_related_name = reverse_related_name
        self.accessor = accessor
        self.pagination = pagination
        self.filterset_class = filterset_class
        self.filter_kwargs = filter_kwargs
        self.request = request
        # kwargs carries pagination kwargs
        self.kwargs = kwargs
        return super().load(key)

    def batch_load_fn(self, keys):
        # queryset by related names
        reverse_related_name = self.reverse_related_name or get_related_name(self.child, self.parent)

        filtered_qs = self.filterset_class(
            data=self.filter_kwargs,
            request=self.request
        ).qs

        qs = self.parent.objects.filter(
            id__in=keys
        ).annotate(
            count=Subquery(
                filtered_qs.filter(**{
                    reverse_related_name: OuterRef('pk')
                }).order_by().values(
                    reverse_related_name
                ).annotate(
                    c=Count('*')
                ).values('c'),
                output_field=IntegerField()
            )
        ).values_list('id', 'count')

        related_objects_by_parent = {id_: count for id_, count in qs}

        return Promise.resolve([
            related_objects_by_parent.get(key) or 0 for key in keys
        ])


class OneToManyLoader(DataLoader):
    """

    Class OneToManyLoader

    A data loader class that loads related objects in a one-to-many relationship.

    Attributes:
    - parent: The parent model class.
    - child: The child model class.
    - related_name: The name of the related field in the parent model (defaults to None).
    - reverse_related_name: The name of the reverse related field in the child model (defaults to None).
    - accessor: A custom accessor function to retrieve the related objects (defaults to None).
    - pagination: The pagination class to use for paginating the related objects (defaults to None).
    - filterset_class: The filterset class to use for filtering the related objects (defaults to None).
    - filter_kwargs: The filter kwargs to use for filtering the related objects (defaults to None).
    - request: The current request object (defaults to None).

    Methods:
    - load(key, parent, child, related_name=None, reverse_related_name=None, accessor=None, pagination=None,
    filterset_class=None, filter_kwargs=None, request=None, **kwargs):
      Loads the related objects for the given key and returns the result.

    - batch_load_fn(keys):
      Loads the related objects for the batch of keys and returns the result.

    """
    def load(
        self,
        key,
        parent,
        child,
        related_name=None,
        reverse_related_name=None,
        accessor=None,
        pagination=None,
        filterset_class=None,
        filter_kwargs=None,
        request=None,
        **kwargs
    ):
        self.parent = parent
        self.child = child
        self.related_name = related_name
        self.reverse_related_name = reverse_related_name
        self.accessor = accessor
        self.pagination = pagination
        self.filterset_class = filterset_class
        self.filter_kwargs = filter_kwargs
        self.request = request
        # kwargs carries pagination kwargs
        self.kwargs = kwargs
        return super().load(key)

    def batch_load_fn(self, keys):
        related_objects_by_parent = defaultdict(list)

        # queryset by related names
        related_name = self.related_name or get_related_name(self.parent, self.child)
        reverse_related_name = self.reverse_related_name or get_related_name(self.child, self.parent)

        # pre-ready the filtered and paginated queryset
        filtered_qs = self.filterset_class(
            data=self.filter_kwargs,
            request=self.request,
        ).qs.filter(**{
            reverse_related_name: OuterRef(reverse_related_name)
        })
        filtered_paginated_qs = self.pagination.paginate_queryset(
            filtered_qs,
            **self.kwargs
        ).values('id')

        OUT_RELATED_FIELD = 'out_related_field'

        prefetch = Prefetch(
            related_name,
            queryset=self.child.objects.filter(
                id__in=Subquery(
                    filtered_paginated_qs
                )
            ).distinct(),
            to_attr=OUT_RELATED_FIELD,
        )

        # FIXME: this prefetch is causing un-necessary join in generated queries
        qs = self.parent.objects.filter(id__in=keys).prefetch_related(prefetch)

        for each in qs:
            related_objects_by_parent[each.id] = getattr(each, OUT_RELATED_FIELD)

        return Promise.resolve([
            related_objects_by_parent.get(key, []) for key in keys
        ])
