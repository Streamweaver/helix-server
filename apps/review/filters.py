from django_filters import rest_framework as df
from utils.filters import IDListFilter, StringListFilter
from apps.review.models import UnifiedReviewComment


class UnifiedReviewCommentFilter(df.FilterSet):
    """

    The `UnifiedReviewCommentFilter` class is a subclass of `df.FilterSet` and is used for filtering instances of the `UnifiedReviewComment` model.

    Attributes:
        events (IDListFilter): A filter for filtering by event IDs.
        figures (IDListFilter): A filter for filtering by figure IDs.
        fields (StringListFilter): A filter for filtering by field names.

    Methods:
        filter_events(qs, name, value):
            Filters the queryset `qs` based on the event IDs in the `value` list.

        filter_figures(qs, name, value):
            Filters the queryset `qs` based on the figure IDs in the `value` list.

        filter_fields(qs, name, value):
            Filters the queryset `qs` based on the field names in the `value` list.

    Meta:
        model: Specifies the model class to be used for filtering (UnifiedReviewComment).
        fields: Specifies the fields that can be filtered on (is_edited, is_deleted).

    Note:
        This class does not return any example code and does not include @author and @version tags.
    """
    events = IDListFilter(method='filter_events')
    figures = IDListFilter(method='filter_figures')
    fields = StringListFilter(method='filter_fields')

    def filter_events(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(event__in=value)

    def filter_figures(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(figure__in=value)

    def filter_fields(self, qs, name, value):
        if value:
            if isinstance(value[0], int):
                return qs.filter(field__in=value).distinct()
            return qs.filter(field__in=[
                UnifiedReviewComment.REVIEW_FIELD_TYPE.get(item).value for item in value
            ])
        return qs

    class Meta:
        model = UnifiedReviewComment
        fields = ('is_edited', 'is_deleted')
