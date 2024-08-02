from django.db.models import (
    Exists,
    Subquery,
    OuterRef,
    Q,
    F,
    When,
    Case,
    Value,
    BooleanField,
)
from django_filters import rest_framework as df

from apps.report.models import Report, ReportGeneration, ReportApproval, ReportComment
from utils.filters import IDListFilter, StringListFilter, generate_type_for_filter_set


class ReportFilter(df.FilterSet):
    """

    The ReportFilter class is a subclass of df.FilterSet and is used to filter the queryset of Report objects.

    Attributes:
        - filter_figure_countries: IDListFilter - a filter for filtering reports by countries.
        - review_status: StringListFilter - a filter for filtering reports by review status.
        - start_date_after: DateFilter - a filter for filtering reports by start date.
        - end_date_before: DateFilter - a filter for filtering reports by end date.
        - is_public: BooleanFilter - a filter for filtering reports by public visibility.
        - is_gidd_report: BooleanFilter - a filter for filtering reports by GIDD report status.
        - is_pfa_visible_in_gidd: BooleanFilter - a filter for filtering reports by PFA visibility in GIDD.

        Meta:
            - model: Report - the model class to filter.
            - fields: a dictionary specifying the fields to filter and the filter options for each field.

    Methods:
        - filter_countries(qs, name, value): filters the queryset qs by the selected countries.
        - filter_by_review_status(qs, name, value): filters the queryset qs by the selected review status.
        - filter_date_after(qs, name, value): filters the queryset qs by the start date.
        - filter_end_date_before(qs, name, value): filters the queryset qs by the end date.
        - filter_is_public(qs, name, value): filters the queryset qs by the public visibility.
        - filter_is_gidd_report(qs, name, value): filters the queryset qs by the GIDD report status.
        - filter_is_pfa_visible_in_gidd(qs, name, value): filters the queryset qs by the PFA visibility in GIDD.

        - qs: a property that returns the filtered queryset based on the filter options.

    Note: This class does not return a queryset by default if the filter is not applied. To include private reports in
    the queryset by default, the `is_public` filter option should be set to None in the filter form.

    """
    filter_figure_countries = IDListFilter(method='filter_countries')
    review_status = StringListFilter(method='filter_by_review_status')
    start_date_after = df.DateFilter(method='filter_date_after')
    end_date_before = df.DateFilter(method='filter_end_date_before')
    is_public = df.BooleanFilter(method='filter_is_public')
    is_gidd_report = df.BooleanFilter(method='filter_is_gidd_report')
    is_pfa_visible_in_gidd = df.BooleanFilter(method='filter_is_pfa_visible_in_gidd')

    class Meta:
        model = Report
        fields = {
            'name': ['unaccent__icontains'],
            'change_in_source': ['exact'],
            'change_in_methodology': ['exact'],
            'change_in_data_availability': ['exact'],
            'retroactive_change': ['exact']
        }

    def filter_countries(self, qs, name, value):
        if value:
            return qs.filter(filter_figure_countries__in=value).distinct()
        return qs

    def filter_by_review_status(self, qs, name, value):
        if not value:
            return qs
        qs = qs.annotate(
            _last_generation_id=Subquery(
                ReportGeneration.objects.filter(
                    report=OuterRef('pk')
                ).order_by('-created_by').values('pk')[:1]
            )
        ).annotate(
            # is_signed_off already exists
            _is_signed_off=F('is_signed_off'),
            _is_approved=Exists(
                ReportApproval.objects.filter(
                    generation=OuterRef('_last_generation_id'),
                    is_approved=True,
                )
            ),
        ).annotate(
            _is_unapproved=Case(
                When(
                    Q(_is_approved=False) & Q(_is_signed_off=False),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        )
        _temp = qs.none()
        if Report.REPORT_REVIEW_FILTER.SIGNED_OFF.name in value:
            signed_off = qs.filter(_is_signed_off=True)
            _temp = _temp | signed_off
        if Report.REPORT_REVIEW_FILTER.APPROVED.name in value:
            approved = qs.filter(_is_approved=True)
            _temp = _temp | approved
        if Report.REPORT_REVIEW_FILTER.UNAPPROVED.name in value:
            unapproved = qs.filter(_is_unapproved=True)
            _temp = _temp | unapproved
        return _temp

    def filter_date_after(self, qs, name, value):
        if value:
            return qs.filter(filter_figure_start_after__gte=value)
        return qs

    def filter_end_date_before(self, qs, name, value):
        if value:
            return qs.filter(filter_figure_end_before__lte=value)
        return qs

    def filter_is_public(self, qs, name, value):
        if value is True:
            return qs.filter(is_public=True)
        if value is False:
            user = self.request.user
            return qs.filter(is_public=False, created_by=user)
        return qs

    def filter_is_gidd_report(self, qs, name, value):
        if value is True:
            return qs.filter(is_gidd_report=True)
        if value is False:
            return qs.filter(is_gidd_report=False)
        return qs

    def filter_is_pfa_visible_in_gidd(self, qs, name, value):
        if value is True:
            return qs.filter(is_pfa_visible_in_gidd=True)
        if value is False:
            return qs.filter(is_pfa_visible_in_gidd=False)
        return qs

    @property
    def qs(self):
        # Return private reports by default if filter is not applied
        is_public = self.data.get('is_public')
        if is_public is None:
            user = self.request.user
            return super().qs.filter(
                Q(is_public=True) | Q(is_public=False, created_by=user)
            )

        return super().qs.distinct()


class DummyFilter(df.FilterSet):
    """
    Class DummyFilter:

        Inherits from df.FilterSet

        Description:
            This class defines a DummyFilter that can be used to filter data based on the 'id' field using an exact
            match.

        Attributes:
            id (df.CharFilter):
                A CharFilter instance that filters data based on the 'id' field using an exact match.

    """
    id = df.CharFilter(field_name='id', lookup_expr='exact')


class ReportApprovalFilter(df.FilterSet):
    """
    The `ReportApprovalFilter` class is a subclass of `FilterSet` that provides filtering capabilities for the
    `ReportApproval` model. It allows filtering based on the `is_approved` field.

    Attributes:
        - model: The model that the filter is applied on.
        - fields: The fields on which the filter is allowed.

    Example usage:
    ```python
    # Create an instance of the ReportApprovalFilter
    filter = ReportApprovalFilter(data=request.GET, queryset=ReportApproval.objects.all())

    # Apply the filter
    filtered_queryset = filter.qs
    ```
    """
    class Meta:
        model = ReportApproval
        fields = ('is_approved',)


class ReportGenerationFilter(df.FilterSet):
    """
    Class: ReportGenerationFilter

    Inherits from: df.FilterSet

    Purpose:
    This class is a filter set used for generating reports based on specified filters.

    Attributes:
    - model (class): The model class for which the filter set is defined.
    - fields (tuple): The fields on which filters will be applied.

    Usage:

    1. Instantiate the ReportGenerationFilter class:

        filter_set = ReportGenerationFilter()

    2. Apply filters using the filter set:

        filtered_results = filter_set.filter(query_params)

    3. Retrieve filtered results:

        for result in filtered_results:
            # Perform required operations on the result

    Note:
    - This class is specifically designed for working with the ReportGeneration model.
    - The 'fields' attribute specifies the fields on which filters can be applied.
    - This class is part of the df (Django Filters) library.

    """
    class Meta:
        model = ReportGeneration
        fields = ('report',)


class ReportCommentFilter(df.FilterSet):
    """
    Filter class for filtering report comments.

    This class extends the `df.FilterSet` class and provides filters for the `ReportComment` model.

    Attributes:
        ids (IDListFilter): Filter for filtering report comments by ID.

    Meta:
        model (ReportComment): The model class to be filtered.
        fields (list): The list of fields in the model that can be filtered.

    """
    ids = IDListFilter(field_name='id')

    class Meta:
        model = ReportComment
        fields = []


ReportFilterDataType, ReportFilterDataInputType = generate_type_for_filter_set(
    ReportFilter,
    'report.schema.report_list',
    'ReportFilterDataType',
    'ReportFilterDataInputType',
)
