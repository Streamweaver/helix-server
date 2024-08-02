import bleach
import django
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import get_storage_class, default_storage
from django.db.models import FileField, TextField
from django.db.models.fields.files import FieldFile
from html import unescape

from helix.storages import FileSystemMediaStorage

StorageClass = get_storage_class()


def generate_full_media_url(path, absolute=False):
    """
    Generate the full media URL for a given file path.

    Parameters:
        path (str): The file path of the media.
        absolute (bool, optional): If set to True, returns the absolute media URL
            which includes the backend base URL. Defaults to False.

    Returns:
        str: The full media URL.

    Example:
        >>> generate_full_media_url('path/to/media.jpg')
        '/media/path/to/media.jpg'

        >>> generate_full_media_url('path/to/media.jpg', absolute=True)
        'https://example.com/media/path/to/media.jpg'
    """
    if not path:
        return ''
    url = default_storage.url(str(path))
    if StorageClass == FileSystemMediaStorage:
        if absolute:
            return f'{settings.BACKEND_BASE_URL}{url}'
    return url


class CachedFieldFile(FieldFile):
    """

    Class: CachedFieldFile

    This class is a subclass of FieldFile.

    Attributes:
    - CACHE_KEY: A class attribute that defines the cache key pattern used for caching the URL of the file.

    Methods:
    - url:
        Returns the URL of the file. If the default file storage is S3Boto3Storage and AWS_QUERYSTRING_AUTH is True, the
        URL is cached using the CACHE_KEY and returned. Otherwise, the URL is fetched using the super() method from
        FieldFile. If the URL is not found in the cache, it is fetched using the super() method and cached for future
        use.

    Example usage:

    file = CachedFieldFile()

    # Get the URL of the file
    url = file.url

    """
    CACHE_KEY = 'url_cache_{}'

    @property
    def url(self):
        if (
            settings.DEFAULT_FILE_STORAGE != 'storages.backends.s3boto3.S3Boto3Storage' or
            getattr(settings, 'AWS_QUERYSTRING_AUTH', False) is False
        ):
            return super().url
        key = self.CACHE_KEY.format(hash(self.name))
        url = cache.get(key)
        if url:
            return url
        url = super().url
        cache.set(key, url, getattr(settings, 'AWS_QUERYSTRING_EXPIRE', 3600))
        return url


class CachedFileField(FileField):
    """

    The `CachedFileField` class is a subclass of `FileField` that adds caching functionality to file uploads in Django.

    Attributes:
        attr_class (object): The class used to store the file and the cache key in the cache backend. It defaults to
        `CachedFieldFile`.

    """
    attr_class = CachedFieldFile


class BleachedTextField(TextField):
    """
    BleachedTextField class extends the TextField class and overrides the get_db_prep_value method to sanitize and
    bleach any user input.

    Methods:
        get_db_prep_value(self, *args, **kwargs) -> Any:
            Overrides the get_db_prep_value method of the TextField class to sanitize and bleach the user input value
            before saving it to the database.

            Parameters:
                *args (Any): Variable-length argument list.
                **kwargs (Any): Keyword arguments.

            Returns:
                Any: The sanitized and bleached value.

            Raises:
                None.
    """
    def get_db_prep_value(self, *args, **kwargs):
        value = super(TextField, self).get_db_prep_value(*args, **kwargs)
        if isinstance(value, str):
            return unescape(bleach.clean(value, strip=True))
        return value


django.db.models.TextField.get_db_prep_value = BleachedTextField.get_db_prep_value
