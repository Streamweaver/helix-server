import json
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import serializers


class IntegerIDField(serializers.IntegerField):
    """

    class IntegerIDField(serializers.IntegerField):

        A custom field for storing integer IDs in the Django REST Framework serializers.

        This field extends the `serializers.IntegerField` class and adds functionality specific to integer IDs.

        Attributes:
            - None

        Methods:
            - None

    """
    pass


class GraphqlSupportDrfSerializerJSONField(serializers.JSONField):
    """
    A custom JSONField serializer for integrating GraphQL support in Django Rest Framework serializers.

    This class extends the base JSONField class provided by the Django Rest Framework serializers module.

    Methods:
    - to_internal_value(data): Converts the given data to its internal representation.

    Attributes:
    - encoder: Optional. The JSON encoder used to encode JSON data. If not provided, the default DjangoJSONEncoder is
    used.

    Usage:
    1. Instantiate the GraphqlSupportDrfSerializerJSONField class and provide any optional parameters.
    2. Use the to_internal_value method to convert external JSON data to internal representation.

    Example:
    ```python
    field = GraphqlSupportDrfSerializerJSONField()
    internal_value = field.to_internal_value(external_data)
    ```
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.encoder = self.encoder or DjangoJSONEncoder

    def to_internal_value(self, data):
        try:
            if self.binary or getattr(data, 'is_json_string', False):
                if isinstance(data, bytes):
                    data = data.decode()
                return json.loads(data, cls=self.decoder)
            else:
                data = json.loads(json.dumps(data, cls=self.encoder))
        except (TypeError, ValueError):
            self.fail('invalid')
        return data
