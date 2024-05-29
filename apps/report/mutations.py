import graphene
from django.utils.translation import gettext

from utils.mutation import generate_input_type_for_serializer
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker
from apps.contrib.serializers import ExcelDownloadSerializer
from apps.contrib.mutations import ExportBaseMutation
from apps.contrib.models import ExcelDownload
from apps.report.models import (
    Report,
    ReportComment,
)
from apps.report.filters import ReportFilterDataInputType
from apps.report.schema import ReportType, ReportCommentType
from apps.report.serializers import (
    ReportSerializer,
    ReportUpdateSerializer,
    ReportCommentSerializer,
    ReportGenerationSerializer,
    ReportApproveSerializer,
    ReportSignoffSerializer,
    check_is_pfa_visible_in_gidd,
)


ReportCreateInputType = generate_input_type_for_serializer(
    'ReportCreateInputType',
    ReportSerializer
)

ReportUpdateInputType = generate_input_type_for_serializer(
    'ReportUpdateInputType',
    ReportUpdateSerializer
)


class CreateReport(graphene.Mutation):
    """
    Class: CreateReport

        A class representing a mutation for creating a report.

    Attributes:
        - data (ReportCreateInputType): The input data for creating a report.
        - errors (List[CustomErrorType]): A list of custom error types.
        - ok (bool): A boolean indicating the success of the mutation.
        - result (ReportType): The created report.

    Methods:
        - mutate(root, info, data): A static method to mutate and create a report.

    Usage:
        mutation = CreateReport(data)
        mutation.mutate(root, info, data)

    """
    class Arguments:
        data = ReportCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportType)

    @staticmethod
    @permission_checker(['report.add_report'])
    def mutate(root, info, data):
        serializer = ReportSerializer(data=data, context=dict(request=info.context.request))
        if errors := mutation_is_not_valid(serializer):
            return CreateReport(errors=errors, ok=False)
        instance = serializer.save()
        return CreateReport(result=instance, errors=None, ok=True)


class UpdateReport(graphene.Mutation):
    """
    This class represents a GraphQL mutation for updating a report.

    Attributes:
    - data: Required argument of type ReportUpdateInputType. Contains the data to update the report.
    - errors: List of CustomErrorType objects. Contains any errors that may have occurred during the mutation.
    - ok: Boolean value indicating the success of the mutation.
    - result: Field of type ReportType. Contains the updated report object.

    Methods:
    - mutate: Static method used to perform the mutation. Updates the specified report using the provided data.

    Example usage:
    mutation {
      updateReport(data: {
        id: 1,
        // Update fields here
      }) {
        errors {
          field
          messages
        }
        ok
        result {
          // Updated report fields here
        }
      }
    }
    """
    class Arguments:
        data = ReportUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportType)

    @staticmethod
    @permission_checker(['report.change_report'])
    def mutate(root, info, data):
        try:
            instance = Report.objects.get(id=data['id'])
        except Report.DoesNotExist:
            return UpdateReport(errors=[
                dict(field='nonFieldErrors', messages=gettext('Report does not exist.'))
            ])
        serializer = ReportSerializer(
            instance=instance, data=data, partial=True, context=dict(request=info.context.request)
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateReport(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateReport(result=instance, errors=None, ok=True)


class DeleteReport(graphene.Mutation):
    """
    The DeleteReport class is a mutation class that is used to delete a report object.

    Attributes:
        errors (graphene.List[graphene.NonNull[CustomErrorType]]): A list of errors encountered during the mutation process.
        ok (graphene.Boolean): A boolean flag indicating whether the mutation was successful.
        result (graphene.Field[ReportType]): The deleted report object.

    Methods:
        mutate(root, info, id): This static method is the entry point for the mutation. It takes in the root, info, and id arguments.
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportType)

    @staticmethod
    @permission_checker(['report.delete_report'])
    def mutate(root, info, id):
        try:
            instance = Report.objects.get(id=id)
        except Report.DoesNotExist:
            return DeleteReport(errors=[
                dict(field='nonFieldErrors', messages=gettext('Report does not exist.'))
            ])

        if not ReportSerializer.has_permission_for_report(
            info.context.request.user,
            instance,
        ):
            return DeleteReport(errors=[
                dict(
                    field='nonFieldErrors',
                    messages=gettext('You do not have permission to edit report.')
                ),
            ])
        instance.delete()
        instance.id = id
        return DeleteReport(result=instance, errors=None, ok=True)


class ReportCommentCreateInputType(graphene.InputObjectType):
    """

    This class represents the input type for creating a report comment.

    Attributes:
        body (str): The body of the comment.
        report (str): The ID of the report associated with the comment.

    """
    body = graphene.String(required=True)
    report = graphene.ID(required=True)


class ReportCommentUpdateInputType(graphene.InputObjectType):
    """
    Input type used for updating a report comment.

    Attributes:
        body (str): The updated body of the comment (required).
        id (str): The identifier of the comment (required).
    """
    body = graphene.String(required=True)
    id = graphene.ID(required=True)


class CreateReportComment(graphene.Mutation):
    """
    CreateReportComment

    A class that represents a GraphQL mutation to create a new report comment.

    Attributes:
        Arguments:
            data (ReportCommentCreateInputType): Required. The input data for creating a report comment.

        errors (List[CustomErrorType]): A list of custom error types.

        ok (bool): A boolean indicating the success of the mutation.

        result (ReportCommentType): The created report comment.

    Methods:
        mutate(root, info, data)
            Static method where the mutation logic is implemented.

            Parameters:
                root: The root value resolved during schema execution.
                info: The GraphQLResolveInfo object containing information about the execution state.
                data (ReportCommentCreateInputType): The input data for creating a report comment.

            Returns:
                A CreateReportComment object with the result and error information.
    """
    class Arguments:
        data = ReportCommentCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportCommentType)

    @staticmethod
    @permission_checker(['report.add_reportcomment'])
    def mutate(root, info, data):
        serializer = ReportCommentSerializer(data=data, context=dict(request=info.context.request))
        if errors := mutation_is_not_valid(serializer):
            return CreateReportComment(errors=errors, ok=False)
        instance = serializer.save()
        return CreateReportComment(result=instance, errors=None, ok=True)


class UpdateReportComment(graphene.Mutation):
    """
    A class used to update a report comment.

    Attributes:
        errors (List[CustomErrorType]): A list of custom error types.
        ok (bool): Indicates if the mutation was successful.
        result (ReportCommentType): The updated report comment.

    Methods:
        mutate(root, info, data): Updates the report comment.

    """
    class Arguments:
        data = ReportCommentUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportCommentType)

    @staticmethod
    @permission_checker(['report.change_reportcomment'])
    def mutate(root, info, data):
        try:
            instance = ReportComment.objects.get(id=data['id'],
                                                 created_by=info.context.user)
        except ReportComment.DoesNotExist:
            return UpdateReportComment(errors=[
                dict(field='nonFieldErrors', messages=gettext('Comment does not exist.'))
            ])
        serializer = ReportCommentSerializer(
            instance=instance, data=data, partial=True, context=dict(request=info.context.request)
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateReportComment(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateReportComment(result=instance, errors=None, ok=True)


class DeleteReportComment(graphene.Mutation):
    """
    Class: DeleteReportComment

        A class that represents a mutation for deleting a report comment.

    Attributes:
        - errors (List[CustomErrorType]): A list of custom error types.
        - ok (bool): A boolean indicating if the mutation was successful or not.
        - result (ReportCommentType): An instance of the deleted report comment.

    Methods:
        - mutate(root, info, id): A static method for executing the mutation.
    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportCommentType)

    @staticmethod
    @permission_checker(['report.delete_reportcomment'])
    def mutate(root, info, id):
        try:
            instance = ReportComment.objects.get(id=id,
                                                 created_by=info.context.user)
        except ReportComment.DoesNotExist:
            return DeleteReportComment(errors=[
                dict(field='nonFieldErrors', messages=gettext('Comment does not exist.'))
            ])
        instance.delete()
        instance.id = id
        return DeleteReportComment(result=instance, errors=None, ok=True)


class GenerateReport(graphene.Mutation):
    """
    This class represents a mutation for generating a report.

    Class: GenerateReport

    Attributes:
    - errors (List[CustomErrorType]): List of custom error types.
    - ok (bool): Flag indicating the success or failure of the mutation.
    - result (ReportType): Field representing the generated report.

    Methods:
    - mutate(root, info, id): Static method used to perform the mutation.

    Dependencies:
    - graphene.Mutation: The base Mutation class provided by the graphene library.
    - graphene.ID: The ID scalar type provided by the graphene library.
    - graphene.List: A List type provided by the graphene library.
    - graphene.NonNull: The NonNull type provided by the graphene library.
    - CustomErrorType: Custom error type specific to the application.
    - ReportType: Type representing a report.
    - permission_checker: Decorator function for checking permissions.
    - Report: Model representing a report.
    - Report.DoesNotExist: Exception raised when a report does not exist.
    - ReportGenerationSerializer: Serializer for generating reports.
    - mutation_is_not_valid: Helper function for checking the validity of a mutation.

    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportType)

    @staticmethod
    @permission_checker(['report.sign_off_report'])
    def mutate(root, info, id):
        try:
            instance = Report.objects.get(id=id)
        except Report.DoesNotExist:
            return GenerateReport(errors=[
                dict(field='nonFieldErrors', messages=gettext('Report does not exist.'))
            ])
        serializer = ReportGenerationSerializer(
            data=dict(report=instance.id),
            context=dict(request=info.context.request),
        )
        if errors := mutation_is_not_valid(serializer):
            return GenerateReport(errors=errors, ok=False)
        serializer.save()
        return GenerateReport(result=instance, errors=None, ok=True)


class SignOffReport(graphene.Mutation):
    """
    The SignOffReport class is a subclass of the graphene.Mutation class. It represents a GraphQL mutation for signing off on a report.

    Attributes:
        Arguments:
            - id (graphene.ID): The ID of the report to be signed off. Required.
            - include_history (graphene.Boolean): Determines whether to include history in the signed off report. Optional.

        errors (graphene.List[CustomErrorType]): List of custom error types encountered during the mutation.
        ok (graphene.Boolean): Indicates whether the mutation was successful or not.
        result (ReportType): The signed off report.

    Methods:
        mutate(root, info, id, include_history): Static method decorator that handles the mutation logic.

    """
    class Arguments:
        id = graphene.ID(required=True)
        include_history = graphene.Boolean(required=False)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportType)

    @staticmethod
    @permission_checker(['report.sign_off_report'])
    def mutate(root, info, id, include_history):
        try:
            instance = Report.objects.get(id=id)
        except Report.DoesNotExist:
            return SignOffReport(errors=[
                dict(field='nonFieldErrors', messages=gettext('Report does not exist.'))
            ])
        serializer = ReportSignoffSerializer(
            data=dict(
                report=id,
                include_history=include_history or False
            ),
            context=dict(request=info.context.request),
        )
        if errors := mutation_is_not_valid(serializer):
            return SignOffReport(errors=errors, ok=False)
        instance = serializer.save()
        instance.refresh_from_db()
        return SignOffReport(result=instance, errors=None, ok=True)


class ApproveReport(graphene.Mutation):
    """
    ApproveReport

    This class is used to handle the mutation for approving a report. It is a subclass of `graphene.Mutation` and contains the necessary arguments, fields, and methods for the mutation.

    Attributes:
        - `errors`: A list of `CustomErrorType` objects. Represents any errors encountered during the mutation.
        - `ok`: A boolean value indicating the success of the mutation.
        - `result`: A `ReportType` object representing the result of the mutation.

    Methods:
        - `mutate`: A static method used to perform the mutation. It takes the `root`, `info`, `id`, and `approve` arguments and returns an instance of `ApproveReport`.

    Example usage:
        >>> mutation = ApproveReport.mutate(root, info, id, approve)
        >>> mutation.ok
        True
        >>> mutation.result
        <ReportType object>

    Note: The example code has been omitted from this documentation.
    """
    class Arguments:
        id = graphene.ID(required=True)
        approve = graphene.Boolean(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportType)

    @staticmethod
    @permission_checker(['report.approve_report'])
    def mutate(root, info, id, approve):
        try:
            instance = Report.objects.get(id=id)
        except Report.DoesNotExist:
            return ApproveReport(errors=[
                dict(field='nonFieldErrors', messages=gettext('Report does not exist.'))
            ])
        serializer = ReportApproveSerializer(
            data=dict(
                report=id,
                is_approved=approve,
            ),
            context=dict(request=info.context.request),
        )
        if errors := mutation_is_not_valid(serializer):
            return ApproveReport(errors=errors, ok=False)
        serializer.save()
        return ApproveReport(result=instance, errors=None, ok=True)


class ExportReports(ExportBaseMutation):
    """

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = ReportFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.REPORT


class ExportReport(graphene.Mutation):
    """
    ExportReport Class

    Class representing a mutation to export a report.

    Attributes:
        errors (List[CustomErrorType]): A list of custom error types.
        ok (bool): Indicates if the mutation was successful.
        result (ReportType): The report type.

    Methods:
        mutate(root, info, id): Static method to perform the mutation.

    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportType)

    @staticmethod
    def mutate(root, info, id):
        from apps.contrib.models import ExcelDownload
        try:
            instance = Report.objects.get(id=id)
        except Report.DoesNotExist:
            return ExportReport(errors=[
                dict(field='nonFieldErrors', messages=gettext('Report does not exist.'))
            ])
        serializer = ExcelDownloadSerializer(
            data=dict(
                download_type=int(ExcelDownload.DOWNLOAD_TYPES.INDIVIDUAL_REPORT),
                filters=dict(),
                model_instance_id=instance.pk
            ),
            context=dict(request=info.context.request)
        )
        if errors := mutation_is_not_valid(serializer):
            return ExportReport(errors=errors, ok=False)
        serializer.save()
        return ExportReport(errors=None, ok=True)


class SetPfaVisibleInGidd(graphene.Mutation):
    """
    Class to set the visibility of PFA (Personal Financial Advisor) in GIDD (Global Investment Decision Database).

    Args:
        SetPfaVisibleInGidd(graphene.Mutation): A subclass of graphene.Mutation.

    Attributes:
        Arguments (class): A subclass of graphene.ObjectType containing the arguments required for the mutation.
            report_id (graphene.ID): A required argument representing the ID of the report.
            is_pfa_visible_in_gidd (graphene.Boolean): A required argument representing the visibility status of the PFA in GIDD.

        errors (graphene.List[graphene.NonNull(CustomErrorType)]): A list of custom error types.
        ok (graphene.Boolean): A boolean representing the success status of the mutation.
        result (graphene.Field(ReportType)): A field representing the updated report object.

    Methods:
        mutate(root, info, report_id, is_pfa_visible_in_gidd): A static method used to perform the mutation.

    """
    class Arguments:
        report_id = graphene.ID(required=True)
        is_pfa_visible_in_gidd = graphene.Boolean(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ReportType)

    @staticmethod
    @permission_checker(['report.update_pfa_visibility_report'])
    def mutate(root, info, report_id, is_pfa_visible_in_gidd):
        report = Report.objects.filter(id=report_id).first()
        if not report:
            return SetPfaVisibleInGidd(errors=[
                dict(field='nonFieldErrors', messages='Report does not exist')
            ])
        if errors := check_is_pfa_visible_in_gidd(report):
            return SetPfaVisibleInGidd(errors=[
                dict(field='nonFieldErrors', messages=errors)
            ])
        if is_pfa_visible_in_gidd is True:
            errors = check_is_pfa_visible_in_gidd(report)
            if errors:
                return SetPfaVisibleInGidd(errors=[
                    dict(field='nonFieldErrors', messages=errors)
                ])
        report.is_pfa_visible_in_gidd = is_pfa_visible_in_gidd
        report.save()
        return SetPfaVisibleInGidd(result=report, errors=None, ok=True)


class Mutation(object):
    """

    The Mutation class provides the following mutation operations for manipulating reports and their comments:

    - create_report: This mutation creates a new report.
    - update_report: This mutation updates an existing report.
    - delete_report: This mutation deletes a report.

    - create_report_comment: This mutation creates a comment on a report.
    - update_report_comment: This mutation updates a comment on a report.
    - delete_report_comment: This mutation deletes a comment on a report.

    - approve_report: This mutation approves a report.
    - start_report_generation: This mutation starts the generation process for a report.
    - sign_off_report: This mutation marks a report as signed off.

    - export_reports: This mutation exports multiple reports.
    - export_report: This mutation exports a single report.
    - set_pfa_visible_in_gidd: This mutation sets the visibility of a report in GIDD.

    Note: This documentation does not contain example code or author/version tags.

    """
    create_report = CreateReport.Field()
    update_report = UpdateReport.Field()
    delete_report = DeleteReport.Field()
    # report comment
    create_report_comment = CreateReportComment.Field()
    update_report_comment = UpdateReportComment.Field()
    delete_report_comment = DeleteReportComment.Field()

    approve_report = ApproveReport.Field()
    start_report_generation = GenerateReport.Field()
    sign_off_report = SignOffReport.Field()
    # export
    export_reports = ExportReports.Field()
    export_report = ExportReport.Field()
    set_pfa_visible_in_gidd = SetPfaVisibleInGidd.Field()
