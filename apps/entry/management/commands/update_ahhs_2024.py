import csv
import datetime
import logging
import os
import typing
from decimal import Decimal
from functools import cached_property

from django.core.management.base import BaseCommand
from django.db import transaction
from requests.structures import CaseInsensitiveDict

from apps.country.models import Country, HouseholdSize
from apps.country.serializers import HouseholdSizeCliImportSerializer
from apps.entry.models import Figure
from apps.users.models import User
from apps.users.utils import HelixInternalBot
from helix.managers import BulkUpdateManager
from utils.common import round_half_up

logger = logging.getLogger(__name__)


def format_date(date: str) -> typing.Union[datetime.datetime, str]:
    try:
        return datetime.datetime.strptime(date, "%d/%m/%Y")
    except ValueError:
        return date


class Command(BaseCommand):

    help = "Update AHHS based on new household size data."

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help="Path to the CSV file containing the data.")

    @cached_property
    def iso3_to_household_sizes_for_2024(self) -> CaseInsensitiveDict:
        """
        Retrieves active household sizes for the year 2024, mapped by their respective countries.
        Returns:
            CaseInsensitiveDict: A dictionary with Country instances as keys and HouseholdSize instances as values.
        """
        household_sizes = HouseholdSize.objects.filter(year=2024, is_active=True).select_related('country')
        return CaseInsensitiveDict({size.country.iso3: size for size in household_sizes})

    @cached_property
    def iso3_to_country_id(self) -> CaseInsensitiveDict:
        """
        Map ISO3 country codes to Country objects.
        Returns:
            CaseInsensitiveDict: Keys are ISO3 codes, values are Country instances.
        """
        countries = Country.objects.filter(iso3__isnull=False)
        return CaseInsensitiveDict({
            iso3: _id
            for _id, iso3 in countries.values_list('id', 'iso3')
        })

    @cached_property
    def admin_user(self) -> User:
        return HelixInternalBot().user

    def create_household_size(self, validated_data: typing.List[dict]):
        for item in validated_data:
            new_ahhs = HouseholdSize.objects.create(
                **item,
            )
            # NOTE: Because of this we haven't used bulk_create
            HouseholdSize.objects.filter(pk=new_ahhs.pk).update(
                created_at=item['created_at'],
                last_modified_by=item['last_modified_by'],
                modified_at=item['modified_at'],
            )
        logger.info(f"Processed {len(validated_data)} new entries.")

    def process_household_size_row(self, row: dict) -> typing.Optional[dict]:
        """
        Convert a CSV row into a dictionary suitable for serialization.
        Args:
            row (Dict[str, str]): The row from CSV file.
        Returns:
            Dict[str, any]: The processed row with country ID.
        """
        country_id = None
        if iso3 := row.get('ISO3'):
            country_id = self.iso3_to_country_id.get(iso3)

        extract_data = {
            'size': row['AHHS'],
            'data_source_category': row['Data source category'],
            'source': row['Source'],
            'source_link': row['Source link'],
        }
        if not all(extract_data.values()):
            logger.warning(f'Skipping due to empty dataset: {row}')
            return

        created_at = format_date(row['Reference date'])
        modified_at = format_date(row['IDMC update date']) or created_at
        return {
            # Data from csv
            **extract_data,
            'country': country_id,
            'year': row['Year'],
            'notes': row['Notes'],
            # Additional metadata
            'created_by': self.admin_user.pk,
            'last_modified_by': self.admin_user.pk,
            'created_at': created_at,
            'modified_at': modified_at,
            'is_active': True,
        }

    def updates_household_sizes_from_csv(self, file_path):
        """
        Processes the CSV file and updates the database.
        """
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            processed_rows = []
            total = 0
            for row in reader:
                total += 1
                if processed_row := self.process_household_size_row(row):
                    processed_rows.append(processed_row)
            self.stdout.write(self.style.NOTICE(f"Processed {len(processed_rows)} out of {total}"))

            serializer = HouseholdSizeCliImportSerializer(data=processed_rows, many=True)
            if serializer.is_valid():
                self.create_household_size(serializer.validated_data)
            else:
                for i, errors in enumerate(serializer.errors):
                    if errors:
                        self.stdout.write(self.style.ERROR(f"---- Error in row {i + 1} ---- "))
                        self.stdout.write(
                            self.style.SUCCESS(f"Row data: {processed_rows[i]}")
                        )
                    for field, error in errors.items():
                        self.stdout.write(
                            self.style.ERROR(f"'{field}': {error}")
                        )
                raise Exception('Import failed')

    def update_figure_with_new_household_size(self, bulk_mgr: BulkUpdateManager, figure: Figure):
        """
        Updates the household size of a figure if it differs from the current size stored.
        Args:
            figure (Figure): The figure object to update.
        """
        logger.debug(f"Updating figure with new household size for {figure.country.iso3}")
        new_household_size = self.iso3_to_household_sizes_for_2024.get(figure.country.iso3)
        if new_household_size is None:
            logger.error(f"No household size found for country {figure.country.iso3}")
            return
        if figure.household_size != new_household_size.size:
            logger.info(f"Figure <{figure.pk}>. Updating household size from "
                        f"{figure.household_size} to {new_household_size.size}")
            figure.household_size = new_household_size.size
            figure.total_figures = round_half_up(figure.reported * Decimal(str(figure.household_size)))
            bulk_mgr.add(figure)

    def update_figures_for_2024(self):
        if hasattr(self, 'iso3_to_household_sizes_for_2024'):
            # Clear out household_sizes cache before updating the figures
            del self.iso3_to_household_sizes_for_2024

        bulk_mgr = BulkUpdateManager(['household_size', 'total_figures'], chunk_size=1000)
        figures = Figure.objects.filter(
            unit=Figure.UNIT.HOUSEHOLD,
            # FIXME: We need to update figures for both triangulation and recommended figures
            role=Figure.ROLE.TRIANGULATION,
            # Year can be calculated from the end_date (for both flow and stock figures)
            end_date__year=2024
        )
        for figure in figures:
            self.update_figure_with_new_household_size(bulk_mgr, figure)

        bulk_mgr.done()
        self.stdout.write(self.style.SUCCESS(f'Bulk update summary: {bulk_mgr.summary()}'))

    @transaction.atomic()
    def handle(self, *args, **kwargs):
        """
        Entry point for processing the CSV file to update Household Size.
        """
        csv_file_path = kwargs['csv_file_path']
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file path does not exist: {csv_file_path}")
            return
        try:
            self.updates_household_sizes_from_csv(csv_file_path)
            self.update_figures_for_2024()
            logger.info("2024 AHHS data updated successfully.")
        except FileNotFoundError:
            logger.error(f"CSV file at {csv_file_path} not found.")
        except Exception:
            logger.error("Failed to update 2024 AHHS data:", exc_info=True)
