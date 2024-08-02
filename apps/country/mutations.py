import graphene

from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.permissions import permission_checker
from apps.contrib.mutations import ExportBaseMutation
from apps.contrib.models import ExcelDownload
from apps.country.schema import (
    SummaryType,
    ContextualAnalysisType,
)
from apps.country.filters import CountryFilterDataInputType, MonitoringSubRegionFilterDataInputType
from apps.country.serializers import SummarySerializer, ContextualAnalysisSerializer
from apps.crisis.enums import CrisisTypeGrapheneEnum


class SummaryCreateInputType(graphene.InputObjectType):
    """
    SummaryCreateInputType

    A class representing input for creating a summary.

    Attributes:
        summary (str): The summary text.
        country (int): The ID of the country.

    """
    summary = graphene.String(required=True)
    country = graphene.ID(required=True)


class ContextualAnalysisCreateInputType(graphene.InputObjectType):
    """

    Class: ContextualAnalysisCreateInputType

        This class represents the input type for creating a contextual analysis in a GraphQL schema.
        It defines the required fields and their types for creating a contextual analysis.

    Attributes:
        update (graphene.String): The update/message for the contextual analysis. (required)
        country (graphene.ID): The ID of the country associated with the contextual analysis. (required)
        publish_date (graphene.Date): The publish date of the contextual analysis. (optional)
        crisis_type (graphene.NonNull(CrisisTypeGrapheneEnum)): The crisis type of the contextual analysis. (required)

    """
    update = graphene.String(required=True)
    country = graphene.ID(required=True)
    publish_date = graphene.Date()
    crisis_type = graphene.NonNull(CrisisTypeGrapheneEnum)


class CreateSummary(graphene.Mutation):
    """

    """
    class Arguments:
        data = SummaryCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(SummaryType)

    @staticmethod
    @permission_checker(['country.add_summary'])
    def mutate(root, info, data):
        serializer = SummarySerializer(data=data,
                                       context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateSummary(errors=errors, ok=False)
        instance = serializer.save()
        return CreateSummary(result=instance, errors=None, ok=True)


class CreateContextualAnalysis(graphene.Mutation):
    """

    The `CreateContextualAnalysis` class is a GraphQL mutation class that allows users to create a contextual analysis.
    It extends the `graphene.Mutation` class and provides a set of arguments, return values, and a mutation method.

    Arguments:
    - `data` - Required input field of type `ContextualAnalysisCreateInputType`. This argument represents the data
    needed to create a contextual analysis.

    Attributes:
    - `errors` - A list of non-null `CustomErrorType` objects. This attribute contains a list of any errors that
    occurred during the mutation process.
    - `ok` - A boolean value indicating the success or failure of the mutation.
    - `result` - A field of type `ContextualAnalysisType`. This attribute contains the created contextual analysis
    object if the mutation was successful.

    Methods:
    - `mutate(root, info, data)` - The mutation method that is called when the mutation is executed. It takes three
    parameters:
      - `root` - The root object of the schema.
      - `info` - An object containing information about the execution state of the query.
      - `data` - The input data required to create the contextual analysis.

      This method performs various operations to create the contextual analysis, such as validating the input data,
      saving the serializer instance, and returning the appropriate response.

    Example usage:
    ```python
    mutation {
      createContextualAnalysis(data: { ... }) {
        result {
          id
          ...
        }
        errors {
          message
          ...
        }
        ok
      }
    }
    ```
    """
    class Arguments:
        data = ContextualAnalysisCreateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(ContextualAnalysisType)

    @staticmethod
    @permission_checker(['country.add_contextualanalysis'])
    def mutate(root, info, data):
        serializer = ContextualAnalysisSerializer(data=data,
                                                  context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return CreateContextualAnalysis(errors=errors, ok=False)
        instance = serializer.save()
        return CreateContextualAnalysis(result=instance, errors=None, ok=True)


class ExportCountries(ExportBaseMutation):
    """
    A class for exporting countries data to Excel format.

    This class extends the ExportBaseMutation class.

    Args:
        ExportBaseMutation (class): The base export mutation class.

    Attributes:
        DOWNLOAD_TYPE (str): The download type for exporting countries data.

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = CountryFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.COUNTRY


class ExportMonitoringSubRegions(ExportBaseMutation):
    """
    A class for exporting monitoring sub-regions data.

    Inherits from ExportBaseMutation.

    Parameters:
        - filters (MonitoringSubRegionFilterDataInputType): Required input data to filter the monitoring sub-regions.

    Constants:
        - DOWNLOAD_TYPE (str): The download type for exporting monitoring sub-regions data.

    """
    class Arguments(ExportBaseMutation.Arguments):
        filters = MonitoringSubRegionFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.MONITORING_SUB_REGION


class Mutation:
    """
    The Mutation class represents the set of available mutation operations.

    Attributes:
        create_summary (Field): The mutation field for creating a summary.
        create_contextual_analysis (Field): The mutation field for creating a contextual analysis.
        export_countries (Field): The mutation field for exporting countries.
        export_monitoring_sub_regions (Field): The mutation field for exporting monitoring sub-regions.
    """
    create_summary = CreateSummary.Field()
    create_contextual_analysis = CreateContextualAnalysis.Field()
    export_countries = ExportCountries.Field()
    export_monitoring_sub_regions = ExportMonitoringSubRegions.Field()
