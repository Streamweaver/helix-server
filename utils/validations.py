from collections import OrderedDict
from django.utils.translation import gettext
from django.db.models.query import QuerySet
from django.conf import settings
import requests


class MissingCaptchaException(Exception):
    """Exception raised when a captcha value is missing.

    This exception is raised when a captcha value is missing in a form submission or any other scenario where a captcha is required.

    Attributes:
        None
    """
    pass


def is_child_parent_dates_valid(
    c_start_date,
    c_end_date,
    p_start_date,
    p_name
) -> OrderedDict:
    """

    Check if the child-parent dates are valid.

    :param c_start_date: Start date of the child.
    :param c_end_date: End date of the child.
    :param p_start_date: Start date of the parent.
    :param p_name: Name of the parent.

    :return: An OrderedDict of errors, if any.

    The function first checks if the child start date, child end date, and parent start date are provided and if the child start date is later than the child end date. If so, it adds errors for both the start date and end date, indicating that the start date should be earlier than the end date.

    If the child start date and parent start date are provided and if the parent start date is later than the child start date, it adds an error for the start date, indicating that the child start date should be after the parent start date.

    Otherwise, it returns an empty OrderedDict, indicating that there are no errors.

    """
    errors = OrderedDict()

    if c_start_date and c_end_date and c_start_date > c_end_date:
        errors['start_date'] = gettext('Choose your start date earlier than end date.')
        errors['end_date'] = gettext('Choose your start date earlier than end date.')
        return errors
    if c_start_date and p_start_date and p_start_date > c_start_date:
        errors['start_date'] = gettext('Choose your start date after %s start date: %s.') % (
            p_name or 'parent',
            p_start_date
        )
    return errors


def is_child_parent_inclusion_valid(data, instance, field, parent_field) -> OrderedDict:
    """

    Check if the child-parent inclusion is valid for a given field.

    :param data: The data from the request.
    :type data: dict
    :param instance: The instance of the model.
    :type instance: object
    :param field: The field to check.
    :type field: str
    :param parent_field: The parent field to check against.
    :type parent_field: str
    :return: The errors encountered during validation.
    :rtype: OrderedDict

    """
    errors = OrderedDict()
    value = data.get(field)
    if not value and instance:
        value = getattr(instance, field, None)
    if hasattr(value, 'all'):  # ManyRelatedManger
        value = value.all()
    if value is not None and type(value) not in (list, tuple, QuerySet):
        value = [value]
    elif value is None:
        value = []
    parent_value = data.get(parent_field.split('.')[0], getattr(instance, parent_field.split('.')[0], None))
    for pf in parent_field.split('.')[1:]:
        parent_value = parent_value.get(pf, None) if hasattr(parent_value, 'get') else getattr(parent_value, pf, None)
    if parent_value:
        if hasattr(parent_value, 'all'):
            parent_value = parent_value.all()
    if parent_value is None:
        parent_value = []
    if set(value).difference(parent_value):
        errors.update({
            field: gettext('%(field_name)s should be one of the following: %(parents)s.') % dict(
                field_name=field.title(),
                parents={", ".join([str(i) for i in parent_value])}
            )
        })
    return errors


def validate_hcaptcha(captcha, site_key):
    """

        Validate hCaptcha

        Validates a user's response to an hCaptcha challenge by making a request to the hCaptcha verification endpoint.

        :param captcha: The user's response to the hCaptcha challenge.
        :type captcha: str
        :param site_key: The site key for the hCaptcha widget.
        :type site_key: str
        :return: True if the user's response is valid, False otherwise.
        :rtype: bool

    """
    CAPTCHA_VERIFY_URL = 'https://hcaptcha.com/siteverify'
    SECRET_KEY = settings.HCAPTCHA_SECRET

    data = {'secret': SECRET_KEY, 'response': captcha, 'sitekey': site_key}
    response = requests.post(url=CAPTCHA_VERIFY_URL, data=data)

    response_json = response.json()
    return response_json['success']
