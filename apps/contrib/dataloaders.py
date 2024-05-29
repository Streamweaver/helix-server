from promise import Promise
from promise.dataloader import DataLoader

from .models import BulkApiOperation


class BulkApiOperationSuccessListLoader(DataLoader):
    """
    This class is a DataLoader subclass that loads success lists of BulkApiOperation instances based on their ids.

    Methods:
    - batch_load_fn(keys): Returns a Promise that resolves to a list of success lists for the specified keys.

    """
    def batch_load_fn(self, keys):
        qs = BulkApiOperation.objects.filter(id__in=keys)
        _map = {}
        for pk, success_list in qs.values_list('id', 'success_list'):
            _map[pk] = success_list
        return Promise.resolve([
            _map.get(key, []) for key in keys
        ])


class BulkApiOperationFailureListLoader(DataLoader):
    """A class to bulk load failure lists for BulkApiOperation objects.

    This class extends the DataLoader class and provides a batch_load_fn method to load failure lists
    for a batch of BulkApiOperation objects.

    Attributes:
        None

    Methods:
        batch_load_fn: Loads failure lists for a batch of BulkApiOperation objects.

    """
    def batch_load_fn(self, keys):
        qs = BulkApiOperation.objects.filter(id__in=keys)
        _map = {}
        for pk, failure_list in qs.values_list('id', 'failure_list'):
            _map[pk] = failure_list
        return Promise.resolve([
            _map.get(key, []) for key in keys
        ])
