import graphene
from graphene_django import DjangoObjectType
from graphene_django_extras import DjangoObjectField
from utils.graphene.enums import EnumDescription

from apps.crisis.enums import CrisisTypeGrapheneEnum
from apps.entry.enums import (
    RoleGrapheneEnum,
    FigureTermsEnum,
    FigureCategoryTypeEnum,
    FigureReviewStatusEnum,
)
from apps.report.models import (
    Report,
    ReportComment,
    ReportApproval,
    ReportGeneration,
)
from apps.report.enums import ReportTypeEnum
from apps.report.filters import (
    ReportFilter,
    ReportApprovalFilter,
    ReportGenerationFilter,
    ReportCommentFilter,
)
from apps.report.enums import ReportGenerationStatusEnum
from utils.graphene.types import CustomDjangoListObjectType
from utils.graphene.fields import DjangoPaginatedListObjectField
from utils.graphene.pagination import PageGraphqlPaginationWithoutCount


class ReportTotalsType(graphene.ObjectType):
    """
    Class representing the totals for different types of reports.

    Attributes:
        total_stock_conflict_sum (int): The total sum of stock conflict reports.
        total_flow_conflict_sum (int): The total sum of flow conflict reports.
        total_stock_disaster_sum (int): The total sum of stock disaster reports.
        total_flow_disaster_sum (int): The total sum of flow disaster reports.
    """
    total_stock_conflict_sum = graphene.Int()
    total_flow_conflict_sum = graphene.Int()
    total_stock_disaster_sum = graphene.Int()
    total_flow_disaster_sum = graphene.Int()


class ReportCommentType(DjangoObjectType):
    """
    A class representing the GraphQL type for a report comment.

    This class is used to define the GraphQL type for a report comment. It is
    based on the DjangoObjectType and maps to the ReportComment model.

    Attributes:
        Meta (class): A class representing the meta options for the GraphQL type.
        model (class): The Django model class that this GraphQL type is based on.

    """
    class Meta:
        model = ReportComment


class ReportCommentListType(CustomDjangoListObjectType):
    """
    This class represents a custom Django list object type for the ReportComment model. It extends the CustomDjangoListObjectType class.

    Attributes:
        - model: The model that this list type is based on (ReportComment).
        - filterset_class: The filterset class to be used for filtering the list query.

    Usage:
    report_comment_list = ReportCommentListType()

    Note:
    This class should be used as a base for creating custom list object types for the ReportComment model.

    """
    class Meta:
        model = ReportComment
        filterset_class = ReportCommentFilter


class ReportApprovalType(DjangoObjectType):
    """
    A class representing the ReportApprovalType in the application.

    Attributes:
        - model (Class): The Django model class associated with the ReportApprovalType.

    Methods:
        None

    """
    class Meta:
        model = ReportApproval


class ReportApprovalListType(CustomDjangoListObjectType):
    """
    ReportApprovalListType class provides a representation of a list of ReportApproval objects in the Django application.

    It inherits from the CustomDjangoListObjectType class and contains customizations specific to the ReportApproval model.

    Attributes:
        - model (class): The Django model class representing the ReportApproval object.
        - filterset_class (class): The Django filterset class to be used for filtering the report approval list.

    Usage:
        # Create an instance of ReportApprovalListType
        report_approval_list = ReportApprovalListType()

        # Access the model attribute
        report_approval_list.model

        # Access the filterset_class attribute
        report_approval_list.filterset_class

    Note: Ensure that the CustomDjangoListObjectType class is defined and imported correctly before using ReportApprovalListType.
    It is recommended to check the CustomDjangoListObjectType class documentation for additional information.
    """
    class Meta:
        model = ReportApproval
        filterset_class = ReportApprovalFilter


class ReportGenerationType(DjangoObjectType):
    """

    The ReportGenerationType class is a DjangoObjectType that represents a report generation in the system. It provides a GraphQL interface to retrieve information about a report generation.

    Attributes:
        - model: The Django model for the report generation.
        - exclude_fields: A list of fields to exclude from the GraphQL interface.

    GraphQL Fields:
        - status: The status of the report generation.
        - status_display: The display value of the status.
        - is_approved: A boolean indicating if the report generation is approved.
        - approvals: A paginated list of ReportApproval objects associated with the report generation.

    Methods:
        - resolve_full_report(root, info, **kwargs): Resolves the full_report field. Returns the absolute URL of the full report if the status of the report generation is COMPLETED, otherwise returns None.
        - resolve_snapshot(root, info, **kwargs): Resolves the snapshot field. Returns the absolute URL of the snapshot if the status of the report generation is COMPLETED, otherwise returns None.

    Example Usage:
        report_generation = ReportGenerationType()
        report_generation.resolve_full_report(root, info, **kwargs)
        report_generation.resolve_snapshot(root, info, **kwargs)
    """
    class Meta:
        model = ReportGeneration
        exclude_fields = ('approvers', )

    status = graphene.NonNull(ReportGenerationStatusEnum)
    status_display = EnumDescription(source='get_status_display')
    is_approved = graphene.Boolean()
    approvals = DjangoPaginatedListObjectField(
        ReportApprovalListType,
    )

    def resolve_full_report(root, info, **kwargs):
        if root.status == ReportGeneration.REPORT_GENERATION_STATUS.COMPLETED:
            return info.context.request.build_absolute_uri(root.full_report.url)
        return None

    def resolve_snapshot(root, info, **kwargs):
        if root.status == ReportGeneration.REPORT_GENERATION_STATUS.COMPLETED:
            return info.context.request.build_absolute_uri(root.snapshot.url)
        return None


class ReportGenerationListType(CustomDjangoListObjectType):
    """
    A class representing a list of report generations.

    This class is a subclass of CustomDjangoListObjectType and is used to define the structure and behavior of a list of report generations.

    Attributes:
        model (Model): The Django model associated with this list type.
        filterset_class (FilterSet): The filter set class to be used for filtering the list.

    """
    class Meta:
        model = ReportGeneration
        filterset_class = ReportGenerationFilter


class ReportType(DjangoObjectType):
    """

    This class represents a ReportType in the system.

    Attributes:
        comments: A field representing the paginated list of comments associated with the report.
        filter_figure_roles: A list of non-null RoleGrapheneEnum values used for filtering the report by figure roles.
        filter_figure_roles_display: A field representing the display value of filter_figure_roles.
        filter_figure_crisis_types: A list of non-null CrisisTypeGrapheneEnum values used for filtering the report by figure crisis types.
        filter_figure_crisis_types_display: A field representing the display value of filter_figure_crisis_types.
        filter_figure_categories: A list of non-null FigureCategoryTypeEnum values used for filtering the report by figure categories.
        filter_figure_terms: A list of non-null FigureTermsEnum values used for filtering the report by figure terms.
        filter_figure_terms_display: A field representing the display value of filter_figure_terms.
        filter_figure_review_status: A list of non-null FigureReviewStatusEnum values used for filtering the report by figure review status.
        total_disaggregation: A non-null ReportTotalsType object representing the total disaggregation of the report.
        last_generation: A field representing the last generation of the report.
        generations: A paginated list of report generations associated with the report.
        generated_from: A field representing the type of report from which this report is generated.
        generated_from_display: A field representing the display value of generated_from.
    """
    class Meta:
        model = Report
        exclude_fields = ('reports', 'figures', 'masterfact_reports')

    comments = DjangoPaginatedListObjectField(ReportCommentListType,
                                              pagination=PageGraphqlPaginationWithoutCount(
                                                  page_size_query_param='pageSize'
                                              ))

    # NOTE: We need to define this at ExtractionQueryObjectType as well
    filter_figure_roles = graphene.List(graphene.NonNull(RoleGrapheneEnum))
    filter_figure_roles_display = EnumDescription(source='get_filter_figure_roles_display')
    filter_figure_crisis_types = graphene.List(graphene.NonNull(CrisisTypeGrapheneEnum))
    filter_figure_crisis_types_display = EnumDescription(source='get_filter_figure_crisis_types_display')
    filter_figure_categories = graphene.List(graphene.NonNull(FigureCategoryTypeEnum))
    filter_figure_terms = graphene.List(graphene.NonNull(FigureTermsEnum))
    filter_figure_terms_display = EnumDescription(source='get_filter_figure_terms_display')
    filter_figure_review_status = graphene.List(graphene.NonNull(FigureReviewStatusEnum))

    total_disaggregation = graphene.NonNull(ReportTotalsType)
    # FIXME: use dataloader for last_generation
    last_generation = graphene.Field(ReportGenerationType)
    generations = DjangoPaginatedListObjectField(
        ReportGenerationListType,
    )
    generated_from = graphene.Field(ReportTypeEnum)
    generated_from_display = EnumDescription(source='get_generated_from_display_display')


class ReportListType(CustomDjangoListObjectType):
    """

    Class: ReportListType

    Inherits From: CustomDjangoListObjectType

    Description:
    This class defines the GraphQL type for a list of reports.

    Attributes:
    - model (class): The Django model class for the Report model.
    - filterset_class (class): The Django filterset class used for filtering the reports.

    """
    class Meta:
        model = Report
        filterset_class = ReportFilter


class Query:
    """
    The Query class represents the GraphQL query object used for fetching data from the server.

    Attributes:
        generation (DjangoObjectField): The generation field represents the report generation type.

        report (DjangoObjectField): The report field represents the report type.

        report_list (DjangoPaginatedListObjectField): The report_list field represents the paginated list of reports.

        report_comment (DjangoObjectField): The report_comment field represents the report comment type.

        report_comment_list (DjangoPaginatedListObjectField): The report_comment_list field represents the paginated list
        of report comments.

        report_generation (DjangoObjectField): The report_generation field represents the report generation type.

        report_generation_list (DjangoPaginatedListObjectField): The report_generation_list field represents the paginated
        list of report generations.

    """
    generation = DjangoObjectField(ReportGenerationType)

    report = DjangoObjectField(ReportType)
    report_list = DjangoPaginatedListObjectField(ReportListType,
                                                 pagination=PageGraphqlPaginationWithoutCount(
                                                     page_size_query_param='pageSize'
                                                 ))
    report_comment = DjangoObjectField(ReportCommentType)
    report_comment_list = DjangoPaginatedListObjectField(ReportCommentListType,
                                                         pagination=PageGraphqlPaginationWithoutCount(
                                                             page_size_query_param='pageSize'
                                                         ))
    report_generation = DjangoObjectField(ReportGenerationType)
    report_generation_list = DjangoPaginatedListObjectField(ReportGenerationListType,
                                                            pagination=PageGraphqlPaginationWithoutCount(
                                                                page_size_query_param='pageSize'
                                                            ))
