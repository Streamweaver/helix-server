from django.utils import timezone
import time
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.conf import settings
from djoser.utils import encode_uid
from django.utils.translation import gettext
from rest_framework import serializers

from apps.users.enums import USER_ROLE
from apps.users.utils import get_user_from_activation_token
from apps.users.models import Portfolio
from apps.country.models import MonitoringSubRegion, Country
from apps.contrib.serializers import UpdateSerializerMixin, IntegerIDField
from utils.validations import validate_hcaptcha, MissingCaptchaException

from .tasks import send_email, recalculate_user_roles

User = get_user_model()


class UserPasswordSerializer(serializers.ModelSerializer):
    """

    The UserPasswordSerializer class is a serializer class for handling password changes for a User model.

    Attributes:
        - old_password: A CharField for the old password.
        - new_password: A CharField for the new password.

    Meta:
        - model: Specifies the User model to be used.
        - fields: Specifies the fields to be included in the serializer.

    Methods:
        - validate_old_password: Validates the old password. If the password is invalid, it raises a ValidationError.
        - validate_new_password: Validates the new password using the validate_password function.
        - save: Sets the new password for the User instance and saves it.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ['old_password', 'new_password']

    def validate_old_password(self, password) -> str:
        if not self.instance.check_password(password):
            raise serializers.ValidationError('The password is invalid.')
        return password

    def validate_new_password(self, password) -> str:
        validate_password(password)
        return password

    def save(self, **kwargs):
        self.instance.set_password(self.validated_data['new_password'])
        self.instance.save()


class RegisterSerializer(serializers.ModelSerializer):
    """

    RegisterSerializer class is a serializer class used for registering a user. It is a subclass of the ModelSerializer
    class provided by the Django Rest Framework.

    Attributes:
        - password: A CharField used for storing the user's password. It is required and write-only.
        - captcha: A CharField used for storing the captcha value entered by the user. It is required and write-only.
        - site_key: A CharField used for storing the site key of the captcha. It is required and write-only.
        - Meta: A class attribute specifying the model used for registration and the fields to be serialized.

    Methods:
        - validate_password(password: str) -> str: A method used for validating the password entered by the user. It
        calls the validate_password() function to perform the validation and returns the password.
        - validate_email(email: str) -> str: A method used for validating the email entered by the user. It checks if
        the email is already taken and returns the email if it is not.
        - validate_captcha(captcha: str): A method used for validating the captcha entered by the user. It calls the
        validate_hcaptcha() function to perform the validation and raises a ValidationError if the captcha is invalid.
        - save(**kwargs): A method used for saving the user's registration data. It creates a new User instance with the
        validated data and returns the instance.

    Note: This class assumes the existence of the User model and the validate_password(), validate_hcaptcha(), and
    gettext() functions used in the code.

    """
    password = serializers.CharField(required=True, write_only=True)
    captcha = serializers.CharField(required=True, write_only=True)
    site_key = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'captcha', 'site_key']

    def validate_password(self, password) -> str:
        validate_password(password)
        return password

    def validate_email(self, email) -> str:
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('The email is already taken.')
        return email

    def validate_captcha(self, captcha):
        if not validate_hcaptcha(captcha, self.initial_data.get('site_key', '')):
            raise serializers.ValidationError(dict(
                captcha=gettext('The captcha is invalid.')
            ))

    def save(self, **kwargs):
        with transaction.atomic():
            instance = User.objects.create_user(
                first_name=self.validated_data.get('first_name', ''),
                last_name=self.validated_data.get('last_name', ''),
                username=self.validated_data['email'],
                email=self.validated_data['email'],
                password=self.validated_data['password'],
                is_active=False
            )
        return instance


class LoginSerializer(serializers.Serializer):
    """
    Class: LoginSerializer

    Serializer for validating and serializing login data.

    Attributes:
    - email (serializers.EmailField): Required email field for login.
    - password (serializers.CharField): Required password field for login.
    - captcha (serializers.CharField): Optional captcha field for login.
    - site_key (serializers.CharField): Optional site_key field for login.

    Methods:
    - _validate_captcha(attrs): Private method for validating captcha.
    - validate(attrs): Method for validating login data.

    """
    email = serializers.EmailField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    captcha = serializers.CharField(required=False, allow_null=True, write_only=True)
    site_key = serializers.CharField(required=False, allow_null=True, write_only=True)

    def _validate_captcha(self, attrs):
        captcha = attrs.get('captcha')
        site_key = attrs.get('site_key')
        email = attrs.get('email')
        attempts = User._get_login_attempt(email)

        def throttle_login_attempt():
            if attempts >= settings.MAX_CAPTCHA_LOGIN_ATTEMPTS:
                now = time.mktime(timezone.now().timetuple())
                last_tried = User._get_last_login_attempt(email)
                if not last_tried:
                    User._set_last_login_attempt(email, now)
                    raise serializers.ValidationError(
                        gettext('Please try again in %s seconds.') % settings.LOGIN_TIMEOUT
                    )
                elapsed = now - last_tried
                if elapsed < settings.LOGIN_TIMEOUT:
                    raise serializers.ValidationError(
                        gettext('Please try again in %s seconds.') % (settings.LOGIN_TIMEOUT - int(elapsed))
                    )
                else:
                    # reset
                    User._reset_login_cache(email)

        if attempts >= settings.MAX_LOGIN_ATTEMPTS and not captcha:
            raise MissingCaptchaException()
        if attempts >= settings.MAX_LOGIN_ATTEMPTS and captcha and not validate_hcaptcha(captcha, site_key):
            attempts = User._get_login_attempt(email)
            User._set_login_attempt(email, attempts + 1)

            throttle_login_attempt()
            raise serializers.ValidationError(dict(
                captcha=gettext('The captcha is invalid.')
            ))

    def validate(self, attrs):
        self._validate_captcha(attrs)

        email = attrs.get('email', '')
        if User.objects.filter(email__iexact=email, is_active=False).exists():
            raise serializers.ValidationError(gettext('Request an admin to activate your account.'))
        user = authenticate(email=email,
                            password=attrs.get('password', ''))
        if not user:
            attempts = User._get_login_attempt(email)
            User._set_login_attempt(email, attempts + 1)
            raise serializers.ValidationError('The email or password is invalid.')
        attrs.update(dict(user=user))
        User._reset_login_cache(email)
        return attrs


class ActivateSerializer(serializers.Serializer):
    """

    ActivateSerializer class is a subclass of serializers.Serializer and is used for activating a user account by
    validating and saving user data.

    Attributes:
    - uid: A CharField representing the user ID required for activation (write-only).
    - token: A CharField representing the activation token required for activation (write-only).

    Methods:
    - validate(attrs): This method is used to validate the user data and activate the user account. It takes the attrs
    parameter, which is a dictionary containing the user ID and activation token. It returns the validated attributes.

    """
    uid = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        user = get_user_from_activation_token(uid=attrs.get('uid', ''),
                                              token=attrs.get('token', ''))
        if user is None:
            raise serializers.ValidationError(gettext('Activation link is not valid.'))
        user.is_active = True
        user.save()
        return attrs


# Begin Portfolios


class MonitoringExpertPortfolioSerializer(serializers.ModelSerializer):
    """

    Class: MonitoringExpertPortfolioSerializer

    Serializes and deserializes the Monitoring Expert portfolio data.

    Attributes:
    - country: PrimaryKeyRelatedField: A field that represents the related country for the portfolio.
    - Meta: Meta class that specifies the model and fields for serialization.

    Methods:
    - validate(attrs: dict) -> dict:
      Validates the serializer data and performs additional validation.
      Parameters:
        - attrs: dict: The serializer data dictionary.
      Returns:
        - dict: The validated data dictionary.

    """
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), required=True)

    def validate(self, attrs: dict) -> dict:
        attrs['role'] = USER_ROLE.MONITORING_EXPERT
        return attrs

    class Meta:
        model = Portfolio
        fields = ['user', 'country']


class BulkMonitoringExpertPortfolioSerializer(serializers.Serializer):
    """

    BulkMonitoringExpertPortfolioSerializer

    Class responsible for serializing and validating bulk monitoring expert portfolio data.

    Attributes:
    - portfolios: MonitoringExpertPortfolioSerializer - Serializer for monitoring expert portfolios.
    - region: PrimaryKeyRelatedField - Field for the monitoring sub region.

    Methods:
    - _validate_region_countries(attrs: dict) -> None:
        Validates if all the provided countries belong to the region.

        Parameters:
        - attrs: dict - Dictionary of attributes for validation.

    - _validate_can_add(attrs: dict) -> None:
        Validates if the user is allowed to add portfolios to the region.

        Parameters:
        - attrs: dict - Dictionary of attributes for validation.

    - validate(attrs: dict) -> dict:
        Validates the attributes of the serializer.

        Parameters:
        - attrs: dict - Dictionary of attributes for validation.

        Returns:
        - dict - Validated attributes.

    - save(*args, **kwargs):
        Saves the validated portfolios and updates the user roles.
    """
    portfolios = MonitoringExpertPortfolioSerializer(many=True)
    region = serializers.PrimaryKeyRelatedField(
        queryset=MonitoringSubRegion.objects.all()
    )

    def _validate_region_countries(self, attrs: dict) -> None:
        # check if all the provided countries belong to the region
        portfolios = attrs.get('portfolios', [])
        regions = set([portfolio['country'].monitoring_sub_region for portfolio in portfolios])
        if len(regions) > 1:
            raise serializers.ValidationError('Multiple regions are not allowed', code='multiple-regions')
        if len(regions) and list(regions)[0] != attrs['region']:
            raise serializers.ValidationError('Countries are not part of the region', code='region-mismatch')

    def _validate_can_add(self, attrs: dict) -> None:
        if self.context['request'].user.highest_role == USER_ROLE.ADMIN:
            return
        # FIXME: We should not use highest_role for anything except ADMIN and GUEST
        if self.context['request'].user.highest_role not in [USER_ROLE.REGIONAL_COORDINATOR]:
            raise serializers.ValidationError(
                gettext('You are not allowed to perform this action'),
                code='not-allowed'
            )
        portfolio = Portfolio.get_coordinator(
            ms_region=attrs['region']
        )
        if portfolio is None or self.context['request'].user != portfolio.user:
            raise serializers.ValidationError(
                gettext('You are not allowed to add to this region'),
                code='not-allowed-in-region'
            )

    def validate(self, attrs: dict) -> dict:
        self._validate_can_add(attrs)
        self._validate_region_countries(attrs)
        return attrs

    def save(self, *args, **kwargs):
        with transaction.atomic():
            reset_user_roles_for = []
            for portfolio in self.validated_data['portfolios']:
                instance = Portfolio.objects.get(country=portfolio['country'],
                                                 role=USER_ROLE.MONITORING_EXPERT)
                old_user = instance.user
                instance.user = portfolio['user']
                instance.save()
                if portfolio['user'] != old_user:
                    reset_user_roles_for.append(old_user.pk)
            recalculate_user_roles.delay(reset_user_roles_for)


class RegionalCoordinatorPortfolioSerializer(serializers.ModelSerializer):
    """
    Class: RegionalCoordinatorPortfolioSerializer

    This class is a serializer for the RegionalCoordinatorPortfolio model. It is responsible for serializing and
    deserializing instances of the model for use in views and forms.

    Methods:
    - _validate_can_add()
        - Validates if the current user has the permission to add a regional coordinator portfolio. Raises a
        ValidationError if the user does not have the required permission.

    - validate(attrs: dict) -> dict
        - Validates the input data and returns the validated attributes. This method calls _validate_can_add() to ensure
        the user has the permission to add a regional coordinator portfolio. It also sets the 'role' attribute to
        USER_ROLE.REGIONAL_COORDINATOR and fetches the portfolio instance based on the monitoring sub region and role.

    - save()
        - Saves the serialized data to the database. It calls the superclass's save() method to handle the actual
        saving. After saving, it triggers a background task to recalculate user roles.

    Attributes:
    - Meta
        - A nested class that defines metadata for the serializer. It specifies the model to serializer, the fields to
        include, and extra kwargs for certain fields.

    """
    def _validate_can_add(self) -> None:
        if self.context['request'].user.highest_role != USER_ROLE.ADMIN:
            raise serializers.ValidationError(
                gettext('You are not allowed to perform this action'),
                code='not-allowed'
            )

    def validate(self, attrs: dict) -> dict:
        self._validate_can_add()
        attrs['role'] = USER_ROLE.REGIONAL_COORDINATOR
        self.instance = Portfolio.objects.get(
            monitoring_sub_region=attrs['monitoring_sub_region'],
            role=USER_ROLE.REGIONAL_COORDINATOR,
        )
        return attrs

    def save(self):
        instance = super().save()
        recalculate_user_roles.delay([self.instance.user.pk])
        return instance

    class Meta:
        model = Portfolio
        fields = ['user', 'monitoring_sub_region']
        extra_kwargs = {
            'monitoring_sub_region': dict(required=True, allow_null=False),
        }


class AdminPortfolioSerializer(serializers.Serializer):
    """
    AdminPortfolioSerializer

    Serializer class for managing portfolios of admin users.

    Attributes:
        register (bool): Flag indicating whether to register or unregister a portfolio.
        user (PrimaryKeyRelatedField): Primary key related field for the user associated with the portfolio.

    Methods:
        _validate_unique(attrs: dict) -> None:
            Validates that a unique portfolio does not already exist for the specified user.
            Raises a serializers.ValidationError if a duplicate portfolio is found.

        _validate_is_admin() -> None:
            Validates that the current user has the role of an admin.
            Raises a serializers.ValidationError if the user is not an admin.

        validate(attrs: dict) -> dict:
            Validates the serializer input.
            Calls _validate_is_admin() and _validate_unique(attrs) methods.
            Returns the validated attributes.

        save() -> Any:
            Saves the portfolio based on the validated data.
            If register is True, creates a new portfolio with the specified user and admin role.
            If register is False, deletes the existing portfolio for the specified user and admin role.
            Returns the user associated with the saved portfolio.
    """
    register = serializers.BooleanField(required=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def _validate_unique(self, attrs) -> None:
        if attrs['register'] and Portfolio.objects.filter(
            user=attrs.get('user'),
            role=USER_ROLE.ADMIN,
        ).exclude(
            id=getattr(self.instance, 'id', None)
        ).exists():
            raise serializers.ValidationError(gettext(
                'Portfolio already exists'
            ), code='already-exists')

    def _validate_is_admin(self) -> None:
        if not self.context['request'].user.highest_role == USER_ROLE.ADMIN:
            raise serializers.ValidationError(
                gettext('You are not allowed to perform this action'),
                code='not-allowed'
            )

    def validate(self, attrs: dict) -> dict:
        self._validate_is_admin()
        self._validate_unique(attrs)

        return attrs

    def save(self):
        if self.validated_data['register']:
            Portfolio.objects.create(
                user=self.validated_data['user'],
                role=USER_ROLE.ADMIN
            )
        else:
            p = Portfolio.objects.get(
                user=self.validated_data['user'],
                role=USER_ROLE.ADMIN
            )
            p.delete()

        return self.validated_data['user']


class DirectorsOfficePortfolioSerializer(serializers.Serializer):
    """
    Class: DirectorsOfficePortfolioSerializer

    Description:
    This class is a serializer used for handling the creation and deletion of a portfolio in the director's office. It
    allows registering or unregistering a user for the director's office portfolio.

    Attributes:
    - register (serializers.BooleanField): Indicates whether the user should be registered or unregistered for the
    portfolio.
    - user (serializers.PrimaryKeyRelatedField): The related user object for the portfolio.

    Methods:
    - _validate_unique(attrs: dict) -> None:
        This method validates whether a portfolio with the same user and role (DIRECTORS_OFFICE) already exists. If it
        does, a validation error is raised.

    - _validate_is_admin() -> None:
        This method validates whether the current user performing the action is an admin. If not, a validation error is
        raised.

    - validate(attrs: dict) -> dict:
        This method is called to validate the serializer's fields. It calls the _validate_is_admin() and
        _validate_unique() methods to perform the necessary validations.

    - save() -> Any:
        This method is called to save the validated data. If the `register` field is True, a new portfolio is created
        with the given user and role (DIRECTORS_OFFICE). If `register` is False, the existing portfolio for the user and
        role is retrieved and deleted.

    Returns:
    - user (Any): The validated user object.

    Example usage:
    serializer = DirectorsOfficePortfolioSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    """
    register = serializers.BooleanField(required=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def _validate_unique(self, attrs) -> None:
        if attrs['register'] and Portfolio.objects.filter(
            user=attrs.get('user'),
            role=USER_ROLE.DIRECTORS_OFFICE,
        ).exclude(
            id=getattr(self.instance, 'id', None)
        ).exists():
            raise serializers.ValidationError(gettext(
                'Portfolio already exists'
            ), code='already-exists')

    def _validate_is_admin(self) -> None:
        if not self.context['request'].user.highest_role == USER_ROLE.ADMIN:
            raise serializers.ValidationError(
                gettext('You are not allowed to perform this action'),
                code='not-allowed'
            )

    def validate(self, attrs: dict) -> dict:
        self._validate_is_admin()
        self._validate_unique(attrs)

        return attrs

    def save(self):
        if self.validated_data['register']:
            Portfolio.objects.create(
                user=self.validated_data['user'],
                role=USER_ROLE.DIRECTORS_OFFICE
            )
        else:
            p = Portfolio.objects.get(
                user=self.validated_data['user'],
                role=USER_ROLE.DIRECTORS_OFFICE
            )
            p.delete()

        return self.validated_data['user']


class ReportingTeamPortfolioSerializer(serializers.Serializer):
    """
    Serializer for creating and deleting reporting team portfolios.

    Attributes:
        register (serializers.BooleanField): a boolean field indicating whether to register or delete the portfolio.
        user (serializers.PrimaryKeyRelatedField): a field that represents the related user.

    Methods:
        _validate_unique(attrs) -> None:
            Validates if the user already has a reporting team portfolio.
            Raises a ValidationError if a portfolio already exists for the user.

        _validate_is_admin() -> None:
            Validates if the user making the request is an admin.
            Raises a ValidationError if the user is not an admin.

        validate(attrs: dict) -> dict:
            Validates the serializer's data.
            Calls _validate_is_admin() and _validate_unique(attrs) to perform the validation.
            Returns the validated data.

        save() -> Any:
            Saves the validated data by creating or deleting a reporting team portfolio.
            If register is True in the validated data, creates a new portfolio for the user.
            If register is False, deletes the existing portfolio for the user.
            Returns the user associated with the portfolio.
    """
    register = serializers.BooleanField(required=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def _validate_unique(self, attrs) -> None:
        if attrs['register'] and Portfolio.objects.filter(
            user=attrs.get('user'),
            role=USER_ROLE.REPORTING_TEAM,
        ).exclude(
            id=getattr(self.instance, 'id', None)
        ).exists():
            raise serializers.ValidationError(gettext(
                'Portfolio already exists'
            ), code='already-exists')

    def _validate_is_admin(self) -> None:
        if not self.context['request'].user.highest_role == USER_ROLE.ADMIN:
            raise serializers.ValidationError(
                gettext('You are not allowed to perform this action'),
                code='not-allowed'
            )

    def validate(self, attrs: dict) -> dict:
        self._validate_is_admin()
        self._validate_unique(attrs)

        return attrs

    def save(self):
        if self.validated_data['register']:
            Portfolio.objects.create(
                user=self.validated_data['user'],
                role=USER_ROLE.REPORTING_TEAM
            )
        else:
            p = Portfolio.objects.get(
                user=self.validated_data['user'],
                role=USER_ROLE.REPORTING_TEAM
            )
            p.delete()

        return self.validated_data['user']

# End Portfolios


class UserSerializer(UpdateSerializerMixin, serializers.ModelSerializer):
    """
    UserSerializer class is used for serializing and deserializing User objects. It extends UpdateSerializerMixin and
    serializers.ModelSerializer.

    Attributes:
        id (IntegerField): The ID of the user. Required.

    Meta:
        model (User): The model class that this serializer is based on.
        fields (List[str]): The fields to include in the serialized representation of the user.

    Methods:
        validate_is_active(is_active): Validates the 'is_active' field of the user. Raises a serializers.ValidationError
            if the user being updated is the same as the current user.
        validate(attrs): Validates the entire set of attributes on the user. Raises a serializers.ValidationError
            if the current user is not allowed to update the user being serialized.
        update(instance, validated_data): Updates the user instance with the validated data. Also creates new portfolios
            if any are provided in the validated data.

    """
    id = IntegerIDField(required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'username', 'is_active']

    def validate_is_active(self, is_active):
        if self.instance and self.context['request'].user == self.instance:
            raise serializers.ValidationError(gettext('You cannot activate/deactivate yourself.'))
        return is_active

    def validate(self, attrs):
        if not User.can_update_user(self.instance.id, self.context['request'].user):
            raise serializers.ValidationError(gettext('You are not allowed to update this user.'))
        return attrs

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        portfolios = validated_data.get('portfolios', [])
        if portfolios:
            Portfolio.objects.bulk_create([
                Portfolio(**item, user=instance) for item in portfolios
            ])

        return instance


class GenerateResetPasswordTokenSerializer(serializers.Serializer):
    """

    The GenerateResetPasswordTokenSerializer class is responsible for validating the input data and generating a
    password reset token for a user.

    Attributes:
    - captcha (CharField): A required field representing the captcha value.
    - email (EmailField): A required field representing the user's email.
    - site_key (CharField): A required field representing the site key.

    Methods:
    - validate_captcha(captcha): Validates the captcha value and raises a ValidationError if it is invalid.
    - validate(attrs): Validates the input data and generates a password reset token for the user. If a user with the
    given email exists, it generates the token and sends a password reset email. If no user exists, it raises a
    ValidationError indicating that the user does not exist.

    Note: This class does not provide any example code and does not contain any @author or @version tags.

    """
    captcha = serializers.CharField(required=True, write_only=True)
    email = serializers.EmailField(write_only=True, required=True)
    site_key = serializers.CharField(required=True, write_only=True)

    def validate_captcha(self, captcha):
        if not validate_hcaptcha(captcha, self.initial_data.get('site_key', '')):
            raise serializers.ValidationError(dict(
                captcha=gettext('The captcha is invalid.')
            ))

    def validate(self, attrs):
        email = attrs.get("email", None)
        # if user exists for this email
        try:
            user = User.objects.get(email=email)
            # Generate password reset token and uid
            token = default_token_generator.make_token(user)
            uid = encode_uid(user.pk)
            # Get base url by profile type
            button_url = settings.PASSWORD_RESET_CLIENT_URL.format(
                uid=uid,
                token=token,
            )
            message = gettext(
                "We received a request to reset your Helix account password. "
                "If you wish to do so, please click below. Otherwise, you may "
                "safely disregard this email."
            )
        # if no user exists for this email
        except User.DoesNotExist:
            # explanatory email message
            raise serializers.ValidationError(gettext('User with this email does not exist.'))
        subject = gettext("Reset password request for Helix")
        context = {
            "heading": gettext("Reset Password"),
            "message": message,
            "button_text": gettext("Reset Password"),
        }
        if button_url:
            context["button_url"] = button_url
        transaction.on_commit(lambda: send_email.delay(
            subject, message, [email], html_context=context
        ))
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """

    The ResetPasswordSerializer class is responsible for serializing and validating data related to resetting a
    password.

    Attributes:
    - password_reset_token (CharField): Write-only field for the password reset token.
    - uid (CharField): Write-only field for the user ID.
    - new_password (CharField): Write-only field for the new password.

    Methods:
    - validate_new_password: This method validates the new password by calling the validate_password function and
    returning the password.
    - validate: This method validates the attributes of the serializer. It retrieves the uid, token, and new_password
    from the attributes dictionary. It then calls the get_user_from_activation_token function to retrieve the user
    object. If the user object is None, it raises a serializers.ValidationError with the message 'The token is invalid'.
    Otherwise, it sets the new password for the user and saves the user object. It finally returns the attrs dictionary.
    """

    password_reset_token = serializers.CharField(write_only=True, required=True)
    uid = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, password):
        validate_password(password)
        return password

    def validate(self, attrs):
        uid = attrs.get("uid", None)
        token = attrs.get("password_reset_token", None)
        new_password = attrs.get("new_password", None)
        user = get_user_from_activation_token(uid, token)
        if user is None:
            raise serializers.ValidationError(gettext('The token is invalid.'))
        # set_password also hashes the password that the user will get
        user.set_password(new_password)
        user.save()
        return attrs
