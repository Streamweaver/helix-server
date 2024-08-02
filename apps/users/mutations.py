from django.contrib.auth import login, logout
from django.utils.translation import gettext
from django.conf import settings
import graphene

from apps.contrib.models import ExcelDownload
from apps.contrib.mutations import ExportBaseMutation
from apps.country.models import MonitoringSubRegion
from apps.users.schema import UserType, PortfolioType
from apps.users.models import User, Portfolio
from apps.users.enums import USER_ROLE
from apps.users.serializers import (
    LoginSerializer,
    RegisterSerializer,
    ActivateSerializer,
    UserSerializer,
    UserPasswordSerializer,
    GenerateResetPasswordTokenSerializer,
    ResetPasswordSerializer,
    BulkMonitoringExpertPortfolioSerializer,
    RegionalCoordinatorPortfolioSerializer,
    AdminPortfolioSerializer,
    DirectorsOfficePortfolioSerializer,
    ReportingTeamPortfolioSerializer,
)
from utils.permissions import is_authenticated, permission_checker
from apps.users.filters import UserFilterDataInputType
from utils.error_types import CustomErrorType, mutation_is_not_valid
from utils.mutation import generate_input_type_for_serializer
from utils.validations import MissingCaptchaException

RegisterInputType = generate_input_type_for_serializer(
    'RegisterInputType',
    RegisterSerializer
)


class Register(graphene.Mutation):
    """

    The Register class is a mutation class that is used to register a user in a GraphQL API. It takes in a
    RegisterInputType object as an argument, which contains the data required to register a user.

    Attributes:
    - data (RegisterInputType): The input data required for user registration.
    - errors (List[CustomErrorType]): A list of custom error types.
    - ok (bool): Indicates whether the registration was successful or not.
    - result (UserType): The registered user object.
    - captcha_required (bool): Indicates whether captcha is required or not.

    Methods:
    - mutate: This static method is responsible for registering the user using the provided data. It takes in the root,
    info, and data arguments. The root argument is the root value that was passed at the beginning of the execution, the
    info argument contains information about the execution context, and the data argument is the RegisterInputType
    object containing the user registration data. The method returns a Register object.

    """
    class Arguments:
        data = RegisterInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(UserType)
    captcha_required = graphene.Boolean(required=True, default_value=True)

    @staticmethod
    def mutate(root, info, data):
        serializer = RegisterSerializer(data=data,
                                        context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return Register(errors=errors, ok=False)
        instance = serializer.save()
        return Register(
            result=instance,
            errors=None,
            ok=True
        )


LoginInputType = generate_input_type_for_serializer(
    'LoginInputType',
    LoginSerializer
)


class Login(graphene.Mutation):
    """
    class Login(graphene.Mutation):
        Represents a mutation to perform user login.

        Arguments:
            data (LoginInputType): The input data provided for login.

        Attributes:
            result (graphene.Field): The resulting user if login is successful.
            errors (graphene.List): A list of custom error messages if login fails.
            ok (graphene.Boolean): Indicating whether login was successful or not.
            captcha_required (graphene.Boolean): Indicating whether captcha is required for login.

        Example usage:
            mutation {
                login(
                    data: {
                        email: "example@example.com",
                        password: "password123"
                    }
                ) {
                    result {
                        id
                        name
                        email
                    }
                    errors {
                        field
                        message
                    }
                    ok
                    captcha_required
                }
            }

        Returns:
            Login: The mutated Login object.

        Raises:
            MissingCaptchaException: If captcha is missing from login request.
    """
    class Arguments:
        data = LoginInputType(required=True)

    result = graphene.Field(UserType)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean(required=True)
    captcha_required = graphene.Boolean(required=True, default_value=False)

    @staticmethod
    def mutate(root, info, data):
        serializer = LoginSerializer(data=data,
                                     context={'request': info.context.request})
        try:
            errors = mutation_is_not_valid(serializer)
        except MissingCaptchaException:
            return Login(ok=False, captcha_required=True)
        if errors:
            attempts = User._get_login_attempt(data['email'])
            return Login(
                errors=errors,
                ok=False,
                captcha_required=attempts >= settings.MAX_LOGIN_ATTEMPTS
            )
        if user := serializer.validated_data.get('user'):
            login(info.context.request, user)
        return Login(
            result=user,
            errors=None,
            ok=True
        )


ActivateInputType = generate_input_type_for_serializer(
    'ActivateInputType',
    ActivateSerializer
)


class Activate(graphene.Mutation):
    """
    The Activate class is a Mutation class defined in the Graphene library. It represents a mutation operation that
    activates a certain data input.

    Attributes:
        - Arguments:
            - data: An instance of ActivateInputType, which is a required argument for the mutation.

        - errors: A list of CustomErrorType objects. Each CustomErrorType object represents an error that occurred
        during the activation mutation.

        - ok: A boolean value indicating the success state of the activation mutation.

    Methods:
        - mutate(root, info, data): This static method handles the mutation operation. It takes three parameters:
            - root: The root object of the GraphQL query/mutation.
            - info: The GraphQLResolveInfo object containing information about the mutation.
            - data: The ActivateInputType object containing the data to be activated.

    Returns:
        - An instance of the Activate class with the following attributes:
            - errors: A list of CustomErrorType objects representing any errors that occurred during the mutation.
            - ok: A boolean value indicating the success state of the mutation.

    Usage example:
        # Create an instance of ActivateInputType with the required data
        data = ActivateInputType(required=True)

        # Call the mutate method with the necessary parameters
        result = Activate.mutate(root, info, data)

        # Access the attributes of the result
        errors = result.errors
        ok = result.ok
    """
    class Arguments:
        data = ActivateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info, data):
        serializer = ActivateSerializer(data=data,
                                        context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return Activate(errors=errors, ok=False)
        return Activate(errors=None, ok=True)


class Logout(graphene.Mutation):
    """
    Mutation class for performing user logout.

    Attributes
    ----------
    ok : bool
        Indicates if the logout was successful.

    Methods
    -------
    mutate(info, *args, **kwargs)
        Perform the logout operation.

    Returns
    -------
    Logout
        An instance of the Logout class with the `ok` attribute set to True if the logout was successful.
    """
    ok = graphene.Boolean()

    def mutate(self, info, *args, **kwargs):
        if info.context.user.is_authenticated:
            logout(info.context.request)
        return Logout(ok=True)


UserPasswordInputType = generate_input_type_for_serializer(
    'UserPasswordInputType',
    UserPasswordSerializer
)


class ChangeUserPassword(graphene.Mutation):
    """

    The ChangeUserPassword class is a mutation class that allows users to change their password.

    Arguments:
    - data: This is a required argument of type UserPasswordInputType. It contains the new password data for the user.

    Attributes:
    - errors: A list of CustomErrorType objects. If there are any errors during the mutation process, they will be
    stored in this list.
    - ok: A boolean value indicating the success or failure of the mutation.
    - result: A field of type UserType. It represents the updated user object after the password change.

    Methods:
    - mutate(root, info, data): This is a static method decorated with the @is_authenticated() decorator. It is the main
    method of the mutation class and is responsible for performing the password change. It takes three arguments:
      - root: The root object, which is not used in this method.
      - info: The GraphQL Resolve Info object, which contains information about the executing query and schema.
      - data: The new password data provided by the user.

      Inside the method:
      - A UserPasswordSerializer instance is created with the current user as the instance, the provided password data,
      and the request context.
      - If there are any validation errors, the method "mutation_is_not_valid" is called, and the errors are assigned to
      the "errors" attribute.
      - If there are no errors, the serializer saves the changes and the updated user object is assigned to the "result"
      attribute.
      - Finally, an instance of the ChangeUserPassword class is returned with the appropriate values for the "errors",
      "ok", and "result" attributes.

    Example usage:

    mutation {
      changeUserPassword(data: {
        oldPassword: "old123",
        newPassword: "new456"
      }) {
        ok
        result {
          id
          username
        }
        errors {
          field
          message
        }
      }
    }

    """
    class Arguments:
        data = UserPasswordInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(UserType)

    @staticmethod
    @is_authenticated()
    def mutate(root, info, data):
        serializer = UserPasswordSerializer(instance=info.context.user,
                                            data=data,
                                            context={'request': info.context.request},
                                            partial=True)
        if errors := mutation_is_not_valid(serializer):
            return ChangeUserPassword(errors=errors, ok=False)
        serializer.save()
        return ChangeUserPassword(result=info.context.user, errors=None, ok=True)


UserUpdateInputType = generate_input_type_for_serializer(
    'UserUpdateInputType',
    UserSerializer
)


class UpdateUser(graphene.Mutation):
    """
    The `UpdateUser` class is a mutation class in a GraphQL schema. This class is responsible for updating a user record
    in the database.

    Attributes:
        - `errors`: A list of custom error types, representing any errors encountered during the mutation process.
        - `ok`: A boolean value indicating the success or failure of the mutation.
        - `result`: A field of type `UserType`, representing the updated user record.

    Arguments:
        - `data` (Required): An instance of `UserUpdateInputType`, containing the updated data for the user.

    Methods:
        - `mutate(root, info, data)`: A static method decorated with `is_authenticated()` decorator. It is responsible
        for performing the mutation operation. It takes the following parameters:
            - `root`: The root instance of the mutation class.
            - `info`: An instance of `ResolveInfo` class which provides information about the execution state of the
            GraphQL query.
            - `data`: The updated data for the user.

    Returns:
        - If the user record with the provided ID is not found in the database, returns an instance of `UpdateUser`
        class with the `errors` attribute populated with a custom error dict indicating the user was not found.
        - If the mutation operation is not valid (e.g., invalid input data), returns an instance of `UpdateUser` class
        with the `errors` attribute populated with custom error types and `ok` set to `False`.
        - If the mutation operation is successful, returns an instance of `UpdateUser` class with the `result` attribute
        set to the updated user record, `errors` set to `None`, and `ok` set to `True`.
    """
    class Arguments:
        data = UserUpdateInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(UserType)

    @staticmethod
    @is_authenticated()
    def mutate(root, info, data):
        try:
            user = User.objects.get(id=data['id'])
        except User.DoesNotExist:
            return UpdateUser(
                errors=[
                    dict(field='nonFieldErrors', messages=gettext('User not found.'))
                ]
            )
        serializer = UserSerializer(instance=user,
                                    data=data,
                                    context={'request': info.context.request},
                                    partial=True)
        if errors := mutation_is_not_valid(serializer):
            return UpdateUser(errors=errors, ok=False)
        serializer.save()
        return UpdateUser(result=user, errors=None, ok=True)


GenerateResetPasswordTokenType = generate_input_type_for_serializer(
    'GenerateResetPasswordTokenType',
    GenerateResetPasswordTokenSerializer
)


class GenerateResetPasswordToken(graphene.Mutation):
    """

    Class: GenerateResetPasswordToken

    This class is a mutation class for generating a reset password token. It is used in a GraphQL schema and takes an
    input argument "data" of type GenerateResetPasswordTokenType.

    Attributes:
    - `errors`: A list of CustomErrorType objects representing any errors that occurred during the mutation.
    - `ok`: A boolean value indicating the success or failure of the mutation.

    Methods:
    - `mutate(root, info, data)`: A static method that is called to perform the mutation operation. It takes three
    arguments:
        - `root`: The root object of the GraphQL query/mutation.
        - `info`: An object containing information about the execution of the GraphQL query/mutation.
        - `data`: The input argument of type GenerateResetPasswordTokenType.

    Returns:
    - An instance of the GenerateResetPasswordToken class with the following attributes:
        - `errors`: A list of CustomErrorType objects representing any errors that occurred during the mutation.
        - `ok`: A boolean value indicating the success or failure of the mutation.

    """
    class Arguments:
        data = GenerateResetPasswordTokenType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info, data):
        serializer = GenerateResetPasswordTokenSerializer(data=data)
        if errors := mutation_is_not_valid(serializer):
            return GenerateResetPasswordToken(errors=errors, ok=False)
        return GenerateResetPasswordToken(errors=None, ok=True)


ResetPasswordType = generate_input_type_for_serializer(
    'ResetPasswordType',
    ResetPasswordSerializer
)


class ResetPassword(graphene.Mutation):
    """

    """
    class Arguments:
        data = ResetPasswordType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info, data):
        serializer = ResetPasswordSerializer(data=data)
        if errors := mutation_is_not_valid(serializer):
            return ResetPassword(errors=errors, ok=False)
        return ResetPassword(errors=None, ok=True)


BulkMonitoringExpertPortfolioInputType = generate_input_type_for_serializer(
    'BulkMonitoringExpertPortfolioInputType',
    BulkMonitoringExpertPortfolioSerializer
)

RegionalCoordinatorPortfolioInputType = generate_input_type_for_serializer(
    'RegionalCoordinatorPortfolioInputType',
    RegionalCoordinatorPortfolioSerializer
)

AdminPortfolioInputType = generate_input_type_for_serializer(
    'AdminPortfolioInputType',
    AdminPortfolioSerializer
)

DirectorsOfficePortfolioInputType = generate_input_type_for_serializer(
    'DirectorsOfficePortfolioInputType',
    DirectorsOfficePortfolioSerializer
)

ReportingTeamPortfolioInputType = generate_input_type_for_serializer(
    'ReportingTeamPortfolioInputType',
    ReportingTeamPortfolioSerializer
)


class CreateMonitoringExpertPortfolio(graphene.Mutation):
    """

    CreateMonitoringExpertPortfolio

    This class represents a GraphQL mutation that creates a monitoring expert portfolio.

    Arguments:
    - data: Required argument of type BulkMonitoringExpertPortfolioInputType. Specifies the input data for creating the
    portfolio.

    Properties:
    - errors: List of CustomErrorType. Contains any errors that occurred during the mutation.
    - ok: Boolean. Indicates whether the mutation was successful or not.
    - result: Field of type apps.country.schema.MonitoringSubRegionType. Represents the created monitoring sub-region.

    Methods:
    - mutate(root, info, data): Static method that performs the mutation operation. It takes the following parameters:
        - root: The root resolver object (usually not used).
        - info: The GraphQL ResolveInfo object containing information about the execution state.
        - data: The input data for creating the portfolio.

    This method executes the following steps:
    1. Create a BulkMonitoringExpertPortfolioSerializer object with the provided data and request context.
    2. Check if there are any validation errors using the mutation_is_not_valid function.
    3. If there are errors, return an instance of CreateMonitoringExpertPortfolio with the errors and ok properties set
    accordingly.
    4. Save the serializer to persist the portfolio in the database.
    5. Retrieve the monitoring sub-region object based on the 'region' field in the input data.
    6. Return an instance of CreateMonitoringExpertPortfolio with the result, errors, and ok properties set.

    """
    class Arguments:
        data = BulkMonitoringExpertPortfolioInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field('apps.country.schema.MonitoringSubRegionType')

    @staticmethod
    @permission_checker(['users.add_portfolio'])
    def mutate(root, info, data):
        serializer = BulkMonitoringExpertPortfolioSerializer(
            data=data,
            context={'request': info.context.request}
        )
        if errors := mutation_is_not_valid(serializer):
            return CreateMonitoringExpertPortfolio(errors=errors, ok=False)
        serializer.save()
        return CreateMonitoringExpertPortfolio(
            result=MonitoringSubRegion.objects.get(id=data['region']),
            errors=None,
            ok=True
        )


class UpdateRegionalCoordinatorPortfolio(graphene.Mutation):
    """
    Class: UpdateRegionalCoordinatorPortfolio

    This class represents a GraphQL mutation for updating a regional coordinator's portfolio.

    Attributes:
    - data (Required): The input data for updating the portfolio.

    Returns:
    A mutation response containing the following attributes:
    - errors: A list of custom error types.
    - ok: A boolean indicating if the mutation was successful.
    - result: A field representing the updated monitoring sub-region. (Type is
    'apps.country.schema.MonitoringSubRegionType')

    Methods:
    - mutate: The static method that handles the mutation. It receives the root, info, and data parameters, where:
        - root: The root value of the GraphQL execution.
        - info: A GraphQLResolveInfo object containing information about the execution state.
        - data: The input data for updating the portfolio.

    Returns:
    An instance of UpdateRegionalCoordinatorPortfolio containing the mutation response.

    Exceptions:
    - Portfolio.DoesNotExist: If the portfolio does not exist, an error is returned with the field 'nonFieldErrors' and
    the message 'Portfolio does not exist.'

    Example Usage:
    mutation {
      updateRegionalCoordinatorPortfolio(data: {
        monitoringSubRegion: "ABC"
        role: "REGIONAL_COORDINATOR"
      }) {
        errors {
          field
          messages
        }
        ok
        result {
          ...
        }
      }
    }

    """
    class Arguments:
        data = RegionalCoordinatorPortfolioInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field('apps.country.schema.MonitoringSubRegionType')

    @staticmethod
    @permission_checker(['users.change_portfolio'])
    def mutate(root, info, data):
        try:
            instance = Portfolio.objects.get(
                monitoring_sub_region=data['monitoring_sub_region'],
                role=USER_ROLE.REGIONAL_COORDINATOR
            )
        except Portfolio.DoesNotExist:
            return UpdateRegionalCoordinatorPortfolio(errors=[
                dict(field='nonFieldErrors', messages=gettext('Portfolio does not exist.'))
            ])
        serializer = RegionalCoordinatorPortfolioSerializer(
            instance=instance,
            data=data,
            context={'request': info.context.request},
            partial=True
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateRegionalCoordinatorPortfolio(errors=errors, ok=False)
        instance = serializer.save()
        return UpdateRegionalCoordinatorPortfolio(
            result=instance.monitoring_sub_region,
            errors=None,
            ok=True
        )


class DeletePortfolio(graphene.Mutation):
    """
    Class: DeletePortfolio

    This class represents a mutation in a GraphQL schema for deleting a portfolio.

    Attributes:
    - id (graphene.ID): The ID of the portfolio to be deleted

    Returns:
    - errors (List[CustomErrorType]): A list of errors, if any occurred during the mutation process
    - ok (graphene.Boolean): Indicates whether the deletion was successful or not
    - result (PortfolioType): The deleted portfolio instance

    Static Methods:
    - mutate(root, info, id): Static method to perform the actual deletion of the portfolio

    Example Usage:
    mutation {
      deletePortfolio(id: "12345") {
        errors {
          field
          messages
        }
        ok
        result {
          id
          name
          ...
        }
      }
    }

    """
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(PortfolioType)

    @staticmethod
    @permission_checker(['users.delete_portfolio'])
    def mutate(root, info, id):
        try:
            instance: Portfolio = Portfolio.objects.get(id=id)
        except Portfolio.DoesNotExist:
            return DeletePortfolio(errors=[
                dict(field='nonFieldErrors', messages=gettext('Portfolio does not exist.'))
            ])
        if not instance.user_can_alter(info.context.user):
            return DeletePortfolio(errors=[
                dict(field='nonFieldErrors', messages=gettext('You are not permitted to perform this action.'))
            ])
        instance.delete()
        instance.id = id
        return DeletePortfolio(result=instance, errors=None, ok=True)


class UpdateAdminPortfolio(graphene.Mutation):
    """
    The UpdateAdminPortfolio class is a subclass of graphene.Mutation and is used to update the admin portfolio for a
    user.

    Arguments:
        - data: An instance of AdminPortfolioInputType class which represents the data to be updated for the admin
        portfolio. It is a required argument.

    Attributes:
        - errors: A list of CustomErrorType objects representing any errors that occurred during the mutation.
        - ok: A boolean value indicating whether the mutation was successful or not.
        - result: An instance of UserType representing the updated user with the admin portfolio.

    Methods:
        - mutate: A static method used to perform the mutation. It takes the 'root' argument representing the root
        object, the 'info' argument representing the resolver information, and the 'data' argument representing the
        input data for the mutation. It returns an instance of UpdateAdminPortfolio.

    Permissions:
        - The mutate method has a permission_checker decorator with the required permission 'users.change_portfolio'.
        This ensures that only users with the required permission can perform this mutation.

    Usage example:
        mutation {
          updateAdminPortfolio(data: {
            # input fields here
          }) {
            errors {
              # error fields here
            }
            ok
            result {
              # user fields here
            }
          }
        }
    """
    class Arguments:
        data = AdminPortfolioInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(UserType)

    @staticmethod
    @permission_checker(['users.change_portfolio'])
    def mutate(root, info, data):
        serializer = AdminPortfolioSerializer(
            data=data,
            context={'request': info.context.request},
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateAdminPortfolio(errors=errors, ok=False)
        user = serializer.save()
        return UpdateAdminPortfolio(result=user, errors=None, ok=True)


class UpdateDirectorsOfficePortfolio(graphene.Mutation):
    """
    This class represents a GraphQL mutation for updating the portfolio of the Director's office.

    Attributes:
    - Arguments:
        - data: A required parameter of DirectorsOfficePortfolioInputType, representing the data for updating the
        portfolio.
    - errors: A List of CustomErrorType objects, representing any errors that occurred during the mutation.
    - ok: A Boolean value indicating the success of the mutation.
    - result: A Field of UserType, representing the updated user.

    Methods:
    - mutate(): A static method with the decorator @permission_checker(['users.change_portfolio']). It is responsible
    for executing the mutation logic.
        - Parameters:
            - root: The root object of the mutation.
            - info: The GraphQL ResolveInfo object, containing information about the execution state.
            - data: The data for updating the portfolio.
        - Returns:
            - If the mutation is valid, it saves the updated portfolio and returns an instance of
            UpdateDirectorsOfficePortfolio with the updated user and no errors.
            - If the mutation is not valid, it returns an instance of UpdateDirectorsOfficePortfolio with the errors and
            ok set to False.
    """
    class Arguments:
        data = DirectorsOfficePortfolioInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(UserType)

    @staticmethod
    @permission_checker(['users.change_portfolio'])
    def mutate(root, info, data):
        serializer = DirectorsOfficePortfolioSerializer(
            data=data,
            context={'request': info.context.request},
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateDirectorsOfficePortfolio(errors=errors, ok=False)
        user = serializer.save()
        return UpdateDirectorsOfficePortfolio(result=user, errors=None, ok=True)


class UpdateReportingTeamPortfolio(graphene.Mutation):
    """

    The `UpdateReportingTeamPortfolio` class is a mutation class that is used to update the reporting team portfolio. It
    inherits from `graphene.Mutation` and defines the necessary arguments, fields, and methods to perform the mutation.

    Arguments:
        - `data` : A required argument of type `ReportingTeamPortfolioInputType` that contains the updated data for the
        reporting team portfolio.

    Fields:
        - `errors` : A list of `CustomErrorType` objects. Represents any errors that occurred during the mutation
        process.
        - `ok` : A boolean field indicating whether the mutation was successful or not.
        - `result` : A field of type `UserType` representing the updated user object.

    Methods:
        - `mutate` : A static method decorated with `@staticmethod` that performs the mutation operation. It takes three
        parameters:
            - `root` : The root value or object. Ignored in this mutation.
            - `info` : The mutation info object that provides access to various details about the mutation.
            - `data` : The input data containing the updated reporting team portfolio.

            Inside the `mutate` method, the following operations are performed:
            1. A `ReportingTeamPortfolioSerializer` instance is created with the input data and the current request
            context.
            2. The validation and serialization of the input data is performed by calling the `is_valid` method on the
            serializer object.
            3. If there are any errors, the method returns an instance of `UpdateReportingTeamPortfolio` with the
            `errors` field populated and `ok` set to `False`.
            4. If there are no errors, the serializer's `save` method is called to update the user object with the new
            reporting team portfolio.
            5. The method returns an instance of `UpdateReportingTeamPortfolio` with the `result` field populated with
            the updated user object and `ok` set to `True`.

    Note"""
    class Arguments:
        data = ReportingTeamPortfolioInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(UserType)

    @staticmethod
    @permission_checker(['users.change_portfolio'])
    def mutate(root, info, data):
        serializer = ReportingTeamPortfolioSerializer(
            data=data,
            context={'request': info.context.request},
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateReportingTeamPortfolio(errors=errors, ok=False)
        user = serializer.save()
        return UpdateReportingTeamPortfolio(result=user, errors=None, ok=True)


class ExportUsers(ExportBaseMutation):
    """

    ExportUsers

    The ExportUsers class is a subclass of the ExportBaseMutation class. It is used to export user data in Excel format.

    Attributes:
        DOWNLOAD_TYPE (str): The download type for the export, set to 'USER' for user data.

    Arguments:
        filters (UserFilterDataInputType): Required argument that specifies the filters to apply to the user data before
        exporting.

    """
    class Arguments:
        filters = UserFilterDataInputType(required=True)
    DOWNLOAD_TYPE = ExcelDownload.DOWNLOAD_TYPES.USER


class Mutation(object):
    """

    Mutation class is responsible for defining the mutation operations for the system.

    Attributes:
        - login (obj): Represents the login mutation operation.
        - register (obj): Represents the register mutation operation.
        - activate (obj): Represents the activate mutation operation.
        - logout (obj): Represents the logout mutation operation.
        - update_user (obj): Represents the update user mutation operation.
        - change_password (obj): Represents the change user password mutation operation.
        - generate_reset_password_token (obj): Represents the generate reset password token mutation operation.
        - reset_password (obj): Represents the reset password mutation operation.
        - create_monitoring_expert_portfolio (obj): Represents the create monitoring expert portfolio mutation
        operation.
        - update_regional_coordinator_portfolio (obj): Represents the update regional coordinator portfolio mutation
        operation.
        - delete_portfolio (obj): Represents the delete portfolio mutation operation.
        - update_admin_portfolio (obj): Represents the update admin portfolio mutation operation.
        - update_directors_office_portfolio (obj): Represents the update directors office portfolio mutation operation.
        - update_reporting_team_portfolio (obj): Represents the update reporting team portfolio mutation operation.
        - export_users (obj): Represents the export users mutation operation.

    Note: Each operation attribute represents a specific mutation operation.

    Example Usage:

    mutation = Mutation()
    mutation.login # returns the login mutation operation

    """
    login = Login.Field()
    register = Register.Field()
    activate = Activate.Field()
    logout = Logout.Field()
    update_user = UpdateUser.Field()
    change_password = ChangeUserPassword.Field()
    generate_reset_password_token = GenerateResetPasswordToken.Field()
    reset_password = ResetPassword.Field()
    # portfolio
    create_monitoring_expert_portfolio = CreateMonitoringExpertPortfolio.Field()
    update_regional_coordinator_portfolio = UpdateRegionalCoordinatorPortfolio.Field()
    delete_portfolio = DeletePortfolio.Field()
    update_admin_portfolio = UpdateAdminPortfolio.Field()
    update_directors_office_portfolio = UpdateDirectorsOfficePortfolio.Field()
    update_reporting_team_portfolio = UpdateReportingTeamPortfolio.Field()
    # end portfolio
    # exports
    export_users = ExportUsers.Field()
