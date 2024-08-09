import logging
from operator import itemgetter
from datetime import datetime

from django.utils import timezone

from helix.caches import external_api_cache
from apps.common.utils import REDIS_SEPARATOR


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_external_redis_data(key):
    """

    @return: The cached data from the external Redis server.
    @param key: The key to retrieve data for from the external Redis server.
    """
    return external_api_cache.get(key)


def create_client_track_cache_key(api_type, client_id):
    """
    Create a cache key for storing client track data in Redis.

    Parameters:
    - api_type (str): The type of API used by the client.
    - client_id (str): The unique identifier of the client.

    Returns:
    - str: The cache key for storing the client track data in Redis.
    """
    date_today = timezone.now().strftime('%Y-%m-%d')
    return REDIS_SEPARATOR.join(['trackinfo', date_today, api_type, client_id])


def get_client_tracked_cache_keys():
    """
    Retrieves the cache keys for all client tracked information.

    Returns:
        A list of cache keys associated with client tracked information stored in the external API cache. These cache
        keys follow the 'trackinfo{REDIS_SEPARATOR}*' pattern.

    """
    return external_api_cache.keys(f'trackinfo{REDIS_SEPARATOR}*')


def delete_external_redis_record_by_key(*keys):
    """
    Deletes records from an external Redis cache by the given keys.

    Args:
        *keys: A variable-length argument list of keys to delete.

    Returns:
        A list of results indicating whether each key deletion was successful.

    Example:
        delete_external_redis_record_by_key("key1", "key2", "key3")
    """
    return [
        external_api_cache.delete(key)
        for key in keys
    ]


def track_client(api_type, client_id):
    """
    Increments the counter for tracking the number of times a client ID has been tracked for a specific API type.

    Parameters:
    api_type (str): The type of API the client is being tracked for.
    client_id (str): The identifier of the client being tracked.

    Returns:
    None: This method does not return anything.
    """
    cache_key = create_client_track_cache_key(api_type, client_id)
    try:
        external_api_cache.incr(cache_key)
    except ValueError:
        external_api_cache.set(cache_key, 1, None)


def set_client_ids_in_redis(client_ids):
    """
    Set the client IDs in Redis cache.

    This method sets the provided client IDs in the Redis cache using the key 'client_ids'.

    Parameters:
    client_ids (list): The list of client IDs to be set in the Redis cache.

    Returns:
    bool: True if the client IDs were successfully set in the Redis cache, False otherwise.
    """
    external_api_cache.set('client_ids', client_ids, None)
    return True


def pull_track_data_from_redis(tracking_keys):
    """
    Pulls track data from Redis based on provided tracking keys.

    Parameters:
    - tracking_keys (list): A list of tracking keys to retrieve data from Redis.

    Returns:
    - tracked_data_from_redis (dict): A dictionary containing the tracked data from Redis. The keys are the tracking
    keys and the values are dictionaries with the following keys:
        - api_type (str): The API type.
        - client_id (int): The client ID.
        - tracked_date (date): The tracked date.
        - requests_per_day (int): The number of requests per day.

    Example:
    tracking_keys = ['key1', 'key2']
    pull_track_data_from_redis(tracking_keys) -> {'key1': {'api_type': 'type1', 'client_id': 1, 'tracked_date':
    datetime.date(2021, 1, 1), 'requests_per_day': 100}, 'key2': {'api_type': 'type2', 'client_id': 2, 'tracked_date':
    datetime.date(2021, 2, 2), 'requests_per_day': 200}}
    """
    from apps.contrib.models import Client

    client_mapping = {
        code: _id
        for _id, code in Client.objects.values_list('id', 'code')
    }
    tracked_data_from_redis = {}

    for key in tracking_keys:
        tracked_date, api_type, code = itemgetter(1, 2, 3)(key.split(REDIS_SEPARATOR))
        tracked_date = datetime.strptime(tracked_date, "%Y-%m-%d").date()
        requests_per_day = get_external_redis_data(key)

        # Only save records before today
        if tracked_date >= datetime.now().date():
            continue

        client_id = client_mapping.get(code)
        if client_id is None:
            logger.error(f'Client with is code {code} does not exist.')
            continue

        tracked_data_from_redis[key] = dict(
            api_type=api_type,
            client_id=client_id,
            tracked_date=tracked_date,
            requests_per_day=requests_per_day,
        )
    return tracked_data_from_redis
