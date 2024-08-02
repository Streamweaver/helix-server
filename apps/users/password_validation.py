from django.core.exceptions import ValidationError
from django.utils.translation import ngettext


class MaximumLengthValidator:
    """

    The MaximumLengthValidator class provides a validation method to check if a password exceeds a maximum length and a
    helper method to get the help text for the maximum length requirement.

    Attributes:
        - max_length (int): The maximum length allowed for the password. Defaults to 255 characters.

    Methods:
        - __init__(self, max_length=255):
            Constructor method that initializes the MaximumLengthValidator object with the specified maximum length. If
            no maximum length is provided, it defaults to 255.

        - validate(self, password, user=None):
            Validates the password length and raises a ValidationError if the password length exceeds the maximum
            length. The ValidationError includes an error message and parameters specifying the maximum length.

        - get_help_text(self):
            Returns a help text for the maximum length requirement. The help text includes the maximum length parameter.

    Example usage:
        validator = MaximumLengthValidator(10)
        validator.validate('password')     # Raises a ValidationError if the password length exceeds 10 characters.
        help_text = validator.get_help_text()     # Returns "Your password must contain at most 10 characters."

    """
    def __init__(self, max_length=255):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                ngettext(
                    "This password is too long. It must contain at most %(max_length)d character.",
                    "This password is too long. It must contain at most %(max_length)d characters.",
                    self.max_length
                ),
                code='password_too_long',
                params={'max_length': self.max_length},
            )

    def get_help_text(self):
        return ngettext(
            "Your password must contain at most %(max_length)d character.",
            "Your password must contain at most %(max_length)d characters.",
            self.max_length
        ) % {'max_length': self.max_length}
