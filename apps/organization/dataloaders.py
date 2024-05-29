from collections import defaultdict

from promise import Promise
from promise.dataloader import DataLoader

from .models import Organization


class OrganizationCountriesLoader(DataLoader):
    """
    Class: OrganizationCountriesLoader

    This class is a subclass of DataLoader and is used for loading countries associated with organizations.

    Methods:
    - batch_load_fn(self, keys: list): This method is used to load countries for a given list of organization keys.
        Parameters:
            - keys: A list of organization keys for which countries need to be loaded.
        Returns:
            - A Promise that resolves to a list of countries associated with the given organization keys. The order of the
              countries in the list corresponds to the order of the organization keys provided.

    Example usage:
    loader = OrganizationCountriesLoader()
    countries = loader.batch_load_fn(["org1", "org2"])
    """
    def batch_load_fn(self, keys: list):
        qs = Organization.countries.through.objects.filter(organization__in=keys).select_related('country').only(
            'organization_id',
            'country',
        )
        _map = defaultdict(list)
        for organization in qs:
            _map[organization.organization_id].append(organization.country)
        return Promise.resolve([_map.get(key, []) for key in keys])


class OrganizationOrganizationKindLoader(DataLoader):
    """

    Class: OrganizationOrganizationKindLoader

    A class that loads the organization kind for a list of organization IDs.

    Attributes:
    - None

    Methods:
    - batch_load_fn(keys: list) -> Promise:
        A method that loads the organization kind for a list of organization IDs.

        Parameters:
            - keys (list): A list of organization IDs.

        Returns:
            - Promise: A promise that resolves to a list of organization kinds corresponding to the given organization IDs.

    """
    def batch_load_fn(self, keys: list):
        qs = Organization.objects.filter(id__in=keys).select_related('organization_kind').only(
            'id',
            'organization_kind',
        )
        _map = {}
        for organization in qs.all():
            _map[organization.id] = organization.organization_kind
        return Promise.resolve([_map.get(key) for key in keys])
