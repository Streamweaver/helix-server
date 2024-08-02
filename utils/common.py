import datetime
import traceback
import typing
import functools
import re
import decimal
import tempfile
import logging
from datetime import timedelta

from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets

from helix import redis
from helix.caches import external_api_cache
from apps.contrib.redis_client_track import track_client
from apps.common.utils import EXTERNAL_ARRAY_SEPARATOR


logger = logging.getLogger(__name__)


def convert_date_object_to_string_in_dict(dictionary):
    """

    Converts date object in a nested dictionary to string representation.

    :param dictionary: The nested dictionary to process.
    :type dictionary: dict
    :returns: The nested dictionary with date objects converted to strings.
    :rtype: dict

    The `convert_date_object_to_string_in_dict` function recursively iterates through the nested dictionary and converts
    any date objects (instances of `datetime.date` or `datetime.datetime`) to their string representations using the
    `str()` function. It handles dictionaries within dictionaries and lists of dictionaries, ensuring that all date
    objects are properly converted.

    Example usage:
    ```
    >>> import datetime
    >>> data = {
    ...     'date': datetime.date(2022, 1, 1),
    ...     'nested': {
    ...         'date': datetime.datetime(2022, 1, 1, 12, 0),
    ...         'list': [
    ...             datetime.date(2022, 1, 1),
    ...             {'date': datetime.datetime(2022, 1, 1, 12, 0)}
    ...         ]
    ...     }
    ... }
    >>> convert_date_object_to_string_in_dict(data)
    {'date': '2022-01-01',
     'nested': {'date': '2022-01-01 12:00:00',
                'list': ['2022-01-01', {'date': '2022-01-01 12:00:00'}]}}
    ```
    """
    for key, value in dictionary.items():
        if isinstance(value, (datetime.date, datetime.datetime)):
            dictionary[key] = str(value)
        elif isinstance(value, dict):
            convert_date_object_to_string_in_dict(value)
        elif isinstance(value, list):
            for index, array_value in enumerate(value):
                if isinstance(array_value, dict):
                    convert_date_object_to_string_in_dict(array_value)
                elif isinstance(array_value, (datetime.date, datetime.datetime)):
                    dictionary[key][index] = str(array_value)
    return dictionary


def add_clone_prefix(sentence):
    """

    This method, add_clone_prefix, takes a sentence as input and returns a modified sentence with a prefix added to it.
    The prefix is determined based on the presence of certain patterns in the input sentence.

    :param sentence: The sentence to which the prefix needs to be added.
    :type sentence: str
    :return: The modified sentence with the prefix added.
    :rtype: str

    """
    match = re.match(r"Clone\s*(\d+):\s+(.*)", sentence)
    if match:
        return f"Clone {int(match.group(1)) + 1}: {match.group(2)}"

    match = re.match(r"Clone\s*:\s+(.*)", sentence)
    if match:
        return f"Clone 2: {match.group(1)}"

    return f"Clone: {sentence}"


def is_grid_or_myu_report(start_date, end_date):

    def is_last_day_of_year(date):
        if not date:
            return False
        return date.month == 12 and date.day == 31

    def is_first_day_of_year(date):
        if not date:
            return False
        return date.month == 1 and date.day == 1

    def is_year_equal(start_date, end_date):
        if not start_date:
            return False
        if not end_date:
            return False
        return start_date.year == end_date.year

    def is_last_day_of_sixth_month_in_year(date):
        if not date:
            return False
        return date.month == 6 and date.day == 30

    is_grid_report = (is_first_day_of_year(
        start_date) and is_last_day_of_year(end_date) and is_year_equal(start_date, end_date)
    )
    is_ymu_report = (
        is_first_day_of_year(start_date) and is_last_day_of_sixth_month_in_year(end_date) and
        is_year_equal(start_date, end_date)
    )
    return is_ymu_report or is_grid_report


def get_string_from_list(list_of_string):
    return EXTERNAL_ARRAY_SEPARATOR.join(filter(None, list_of_string))


def get_temp_file(dir=settings.TEMP_FILE_DIRECTORY, **kwargs):
    return tempfile.NamedTemporaryFile(dir=dir, **kwargs)


def get_redis_lock_ttl(lock):
    try:
        return timedelta(seconds=redis.get_connection().ttl(lock.name))
    except Exception:
        pass


def redis_lock(lock_key, timeout=60 * 60 * 4):
    """

    Redis Lock

    Acquire a lock on a Redis key to ensure exclusive access to a critical section of code.

    Parameters:
    - lock_key (str): The Redis key used as the lock identifier.
    - timeout (int): The lock expiration time in seconds (default is 60 * 60 * 4 = 14400 seconds).

    Returns:
    - bool: True if lock acquired successfully, False otherwise.

    """
    def _dec(func):
        def _caller(*args, **kwargs):
            key = lock_key.format(*args, **kwargs)
            lock = redis.get_lock(key, timeout)
            have_lock = lock.acquire(blocking=False)
            if not have_lock:
                logger.warning(f'Unable to get lock for {key}(ttl: {get_redis_lock_ttl(lock)})')
                return False
            try:
                return_value = func(*args, **kwargs) or True
            except Exception:
                logger.error('{}.{}'.format(func.__module__, func.__name__), exc_info=True)
                return_value = False
            lock.release()
            return return_value
        _caller.__name__ = func.__name__
        _caller.__module__ = func.__module__
        return _caller
    return _dec


def round_half_up(float_value):
    """
    Rounds a float value to the nearest integer using the 'round_half_up' method.

    Parameters:
    float_value (float): The float value to be rounded.

    Returns:
    int: The rounded integer value.

    Example:
    >>> round_half_up(3.7)
    4
    >>> round_half_up(2.5)
    3
    >>> round_half_up(4.2)
    4
    """
    return float(
        decimal.Decimal(float_value).quantize(
            0,
            rounding=decimal.ROUND_HALF_UP
        )
    )


def round_and_remove_zero(num):
    """

    Round and Remove Zero

    This method rounds the given number and removes trailing zeros. If the number is None or equal to 0, it returns
    None.

    Parameters:
    - num: The input number to be rounded and have trailing zeros removed.

    Returns:
    - The rounded number with trailing zeros removed, or None if the input is None or equal to 0.

    """
    if num is None or num == 0:
        return None
    absolute_num = abs(num)
    sign = 1 if num > 0 else -1
    if absolute_num <= 100:
        return sign * absolute_num
    if absolute_num <= 1000:
        return sign * round(absolute_num / 10) * 10
    if absolute_num < 10000:
        return sign * round(absolute_num / 100) * 100
    return sign * round(num / 1000) * 1000


def track_gidd(client_id, endpoint_type, viewset: viewsets.GenericViewSet = None):
    """
    Track_Gidd method tracks the client with the provided client_id. It checks if the client_id is registered in the
    external API cache. If not registered, it raises a PermissionDenied exception with a message 'Client is not
    registered.' It then retrieves the client object from the Client model using the client_id. If the client is not
    active, it raises a PermissionDenied exception with a message 'Client is deactivated.' Finally, it calls the
    track_client method to track the client with the specified endpoint_type and client_id.

    Parameters:
    - client_id (string): The unique identifier of the client.
    - endpoint_type (string): The type of endpoint to track.
    - viewset (GenericViewSet, optional): The viewset object. Defaults to None.

    Returns:
    None
    """
    from apps.contrib.models import Client

    if viewset and getattr(viewset, "swagger_fake_view", False):
        # Skip check for swagger view
        return

    if client_id not in external_api_cache.get('client_ids', []):
        raise PermissionDenied('Client is not registered.')

    client = Client.objects.filter(code=client_id).first()
    if not client.is_active:
        raise PermissionDenied('Client is deactivated.')

    # Track client
    track_client(
        endpoint_type,
        client_id,
    )


class RuntimeProfile:
    """

    The `RuntimeProfile` class is used to measure the runtime of a function or code block. It can be used as a decorator
    or as a context manager.

    Usage:
        1. As a decorator:
            @RuntimeProfile()
            def my_function():
                # code to be measured

        2. As a context manager:
            with RuntimeProfile('Label'):
                # code to be measured

    """
    label: str
    start: typing.Optional[datetime.datetime]

    def __init__(self, label: str = 'N/A'):
        self.label = label
        self.start = None

    def __call__(self, func):
        self.label = func.__name__

        @functools.wraps(func)
        def decorated(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return decorated

    def __enter__(self):
        self.start = datetime.datetime.now()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        assert self.start is not None
        time_delta = datetime.datetime.now() - self.start
        logger.info(f'Runtime with <{self.label}>: {time_delta}')


def return_error_as_string(func):
    """
    Decorates a function to return any raised errors as a string, instead of raising them.

    :param func: The function to be decorated.
    :return: A decorated function that returns any raised errors as a string.

    Example Usage:
    ```
    @return_error_as_string
    def divide(a, b):
        return a / b

    result = divide(5, 0)
    print(result)  # Output: 'ZeroDivisionError: division by zero'
    ```
    """
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return traceback.format_exc()
    _wrapper.__name__ = func.__name__
    return _wrapper


client_id = extend_schema(
    parameters=[
        OpenApiParameter(
            "client_id",
            OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
        )
    ],
)
