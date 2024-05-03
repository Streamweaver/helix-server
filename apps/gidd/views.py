import typing
import json
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook
from rest_framework import mixins
from drf_spectacular.utils import extend_schema
from django.db import models
from django.db.models import (
    F, Case, When, Q
)

from apps.country.models import Country
from apps.entry.models import ExternalApiDump, Figure
from apps.common.utils import (
    EXTERNAL_ARRAY_SEPARATOR,
    EXTERNAL_FIELD_SEPARATOR,
)
from apps.crisis.models import Crisis

from .models import (
    Conflict, Disaster, DisplacementData, GiddFigure, IdpsSaddEstimate,
    StatusLog, PublicFigureAnalysis
)
from .serializers import (
    CountrySerializer,
    ConflictSerializer,
    DisaggregationSerializer,
    DisasterSerializer,
    DisplacementDataSerializer,
    PublicFigureAnalysisSerializer,
)
from .rest_filters import (
    DisaggregationFilterSet,
    RestConflictFilterSet,
    RestDisasterFilterSet,
    RestDisplacementDataFilterSet,
    IdpsSaddEstimateFilter,
    PublicFigureAnalysisFilterSet,
)
from utils.common import track_gidd, client_id


@client_id
class ListOnlyViewSetMixin(mixins.ListModelMixin, viewsets.GenericViewSet):
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class CountryViewSet(ListOnlyViewSetMixin):
    serializer_class = CountrySerializer
    lookup_field = 'iso3'
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    filterset_fields = ['id']

    def get_queryset(self):
        track_gidd(
            self.request.GET.get('client_id'),
            ExternalApiDump.ExternalApiType.GIDD_COUNTRY_REST,
            viewset=self,
        )
        return Country.objects.all()


class ConflictViewSet(ListOnlyViewSetMixin):
    serializer_class = ConflictSerializer
    filterset_class = RestConflictFilterSet

    def get_queryset(self):
        track_gidd(
            self.request.GET.get('client_id'),
            ExternalApiDump.ExternalApiType.GIDD_CONFLICT_REST,
            viewset=self,
        )
        return Conflict.objects.all().select_related('country')


class DisasterViewSet(ListOnlyViewSetMixin):
    serializer_class = DisasterSerializer
    filterset_class = RestDisasterFilterSet

    def get_queryset(self):
        api_type = ExternalApiDump.ExternalApiType.GIDD_DISASTER_REST
        if self.action == 'export':
            api_type = ExternalApiDump.ExternalApiType.GIDD_DISASTER_EXPORT_REST

        track_gidd(
            self.request.GET.get('client_id'),
            api_type,
            viewset=self,
        )
        return Disaster.objects.select_related('country')

    @staticmethod
    def get_displacement_status(displacement_occurred: typing.List[int]) -> str:
        if not displacement_occurred:
            return ""
        elif Figure.DISPLACEMENT_OCCURRED.BEFORE.value in displacement_occurred:
            return "Displacement reporting preventive evacuations"
        return "Displacement without preventive evacuations reported"

    @extend_schema(responses=DisasterSerializer(many=True))
    @action(
        detail=False,
        methods=["get"],
        url_path="disaster-export",
        permission_classes=[AllowAny],
    )
    def export(self, request):
        """
        Export disaster
        """
        qs = self.filter_queryset(self.get_queryset())
        wb = Workbook()
        ws = wb.active
        ws.title = "1_Disaster_Displacement_data"
        ws.append([
            'ISO3',
            'Country / Territory',
            'Year',
            'Event Name',
            'Date of Event (start)',
            'Disaster Internal Displacements',
            'Disaster Internal Displacements (Raw)',
            'Hazard Category',
            'Hazard Type',
            'Hazard Sub Type',
            'Event Codes (Code:Type)',
            'Event ID',
            'Displacement occurred',
        ])

        for disaster in qs:
            ws.append(
                [
                    disaster.country.iso3,
                    disaster.country.name,
                    disaster.year,
                    disaster.event_name,
                    disaster.start_date,
                    disaster.new_displacement_rounded,
                    disaster.new_displacement,
                    disaster.hazard_category_name,
                    disaster.hazard_type_name,
                    disaster.hazard_sub_type_name,
                    # FIXME: Remove the fallback using glide_numbers
                    # after GIDD is generated around 2024 May
                    EXTERNAL_ARRAY_SEPARATOR.join(
                        [f"{key}{EXTERNAL_FIELD_SEPARATOR}{value}" for key, value in zip(
                            disaster.event_codes,
                            disaster.event_codes_type
                        )]
                    ) or EXTERNAL_ARRAY_SEPARATOR.join(
                        [f"{key}{EXTERNAL_FIELD_SEPARATOR}Glide Number" for key in disaster.glide_numbers]
                    ),
                    disaster.event_id,
                    self.get_displacement_status(disaster.displacement_occurred),
                ]
            )

        ws2 = wb.create_sheet('README')
        readme_text = [
            ['TITLE: Disasters Global Internal Displacement Database (GIDD)'],
            [],
            ['FILENAME: IDMC_GIDD_Disasters_Internal_Displacement_Data'],
            [],
            ['SOURCE: Internal Displacement Monitoring Centre (IDMC)'],
            [],
            [f'DATE EXTRACTED: {datetime.now().strftime("%B %d, %Y")}'],
            [],
            [f'LAST UPDATE: {StatusLog.last_release_date()}'],
            [],
            ['DESCRIPTION:'],
            [
                'The Internal Displacement Monitoring Centre (IDMC) continuously monitors global displacement events '
                'triggered by conflict, violence, and disasters throughout the year. By collecting and analyzing both '
                'structured and unstructured secondary data from a variety of sources—including government agencies, '
                'UN agencies, and  media—IDMC ensures comprehensive coverage and high data reliability. Data is '
                'disaggregated by type of metric (internal displacements or IDPs), cause, event, location, and data '
                'reliability. Rigorous quality controls are applied to maintain accuracy. The database contains '
                'displacement figures from various countries and regions, covering conflict-induced displacement from '
                '2009 to 2022 and disaster-induced displacement from 2008 to 2022. For detailed definitions and more '
                'robust descriptions, please visit IDMC Monitoring Tools '
                '(https://www.internal-displacement.org/monitoring-tools).'
            ],
            [''],
            ['KEY DEFINITIONS: '],
            [''],
            [
                'Internal Displacements (flows): The estimated total number of internal displacements within the '
                'reporting year. This figure may include individuals displaced multiple times.'
            ],
            [
                'Total Number of IDPs (stocks): Represents the cumulative total of Internally Displaced Persons (IDPs) '
                'at a specific location and point in time, reflecting the total population living in displacement as '
                'of the end of the reporting year.'
            ],
            [
                'USE LICENSE: This content is licensed under CC BY-NC. Detailed licensing information is available at '
                'Creative Commons License.'
            ],
            [''],
            ['COVERAGE: Global'],
            [''],
            ['CONTACT: info@idmc.ch'],
        ]

        for item in readme_text:
            ws2.append(item)
        ws2.append([])
        ws2.append(['DATA DESCRIPTION:'])
        ws2.append([])

        table = [
            ['ISO3: ISO 3166-1 alpha-3. The ISO3 "AB9" was assigned to the Abyei Area.'],
            ['Country / Territory: Short name of the country or territory.'],
            ['Year: The year for which displacement figures are reported.'],
            [
                'Event Name: Common or official event name for the event, if available. Otherwise, events are coded '
                'based on the country, type of hazard, location, and event start date.'
            ],
            ['Date of Event (Start): Approximate start date of the event.'],
            [
                'Disaster Internal Displacements: Total annual rounded figures of internal displacements at the '
                'national level, due to disasters.'
            ],
            [
                'Disaster Internal Displacements (Raw): Unadjusted total figures of internal displacements at the '
                'national level, due to disasters.'
            ],
            ['Hazard Category: Based on the CRED EM-DAT classification.'],
            ['Hazard Type: Hazard type as categorized by CRED EM-DAT.'],
            ['Hazard Sub-Type: Specific sub-type of the hazard as per CRED EM-DAT.'],
            [
                'Event Codes (Code:Type): Unique codes such as the GLIDE number and other database-specific codes used '
                'to identify and track specific events across various databases.'
            ],
            ['Event ID: Unique identifier for events as assigned by IDMC.'],
            ['Displacement Occurred: Indicator for events that included preventive evacuations.'],
        ]
        for item in table:
            ws2.append(item)
        response = HttpResponse(content=save_virtual_workbook(wb))
        filename = 'IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        response['Content-Type'] = 'application/octet-stream'
        return response


class DisplacementDataViewSet(ListOnlyViewSetMixin):
    serializer_class = DisplacementDataSerializer
    filterset_class = RestDisplacementDataFilterSet

    def get_queryset(self):
        api_type = ExternalApiDump.ExternalApiType.GIDD_DISPLACEMENT_REST
        if self.action == 'export':
            api_type = ExternalApiDump.ExternalApiType.GIDD_DISPLACEMENT_EXPORT_REST

        track_gidd(
            self.request.GET.get('client_id'),
            api_type,
            viewset=self,
        )
        return DisplacementData.objects.all()

    def export_conflicts(self, ws, qs):
        ws.append([
            'ISO3',
            'Name',
            'Year',
            'Conflict Stock Displacement',
            'Conflict Stock Displacement (Raw)',
            'Conflict Internal Displacements',
            'Conflict Internal Displacements (Raw)',
        ])
        for item in qs:
            ws.append([
                item.iso3,
                item.country_name,
                item.year,
                item.conflict_total_displacement_rounded,
                item.conflict_total_displacement,
                item.conflict_new_displacement_rounded,
                item.conflict_new_displacement,
            ])

    def export_disasters(self, ws, qs):
        ws.append([
            'ISO3',
            'Name',
            'Year',
            'Disaster Internal Displacements',
            'Disaster Internal Displacements (Raw)',
            'Disaster Stock Displacement',
            'Disaster Stock Displacement (Raw)'
        ])
        for item in qs:
            ws.append([
                item.iso3,
                item.country_name,
                item.year,
                item.disaster_new_displacement_rounded,
                item.disaster_new_displacement,
                item.disaster_total_displacement_rounded,
                item.disaster_total_displacement,
            ])

    def export_displacements(self, ws, qs):
        ws.append([
            'ISO3',
            'Name',
            'Year',
            'Conflict Stock Displacement',
            'Conflict Stock Displacement (Raw)',
            'Conflict Internal Displacements',
            'Conflict Internal Displacements (Raw)',
            'Disaster Internal Displacements',
            'Disaster Internal Displacements (Raw)',
            'Disaster Stock Displacement',
            'Disaster Stock Displacement (Raw)'
        ])
        for item in qs:
            ws.append([
                item.iso3,
                item.country_name,
                item.year,
                item.conflict_total_displacement_rounded,
                item.conflict_total_displacement,
                item.conflict_new_displacement_rounded,
                item.conflict_new_displacement,
                item.disaster_new_displacement_rounded,
                item.disaster_new_displacement,
                item.disaster_total_displacement_rounded,
                item.disaster_total_displacement,
            ])

    @extend_schema(responses=DisplacementDataSerializer(many=True))
    @action(
        detail=False,
        methods=["get"],
        url_path="displacement-export",
        permission_classes=[AllowAny],
    )
    def export(self, request):
        """
        Export displacements, conflict and disaster
        """

        # Track export
        qs = self.filter_queryset(self.get_queryset()).order_by(
            '-year',
            'iso3',
        )

        wb = Workbook()
        ws = wb.active
        # Tab 1
        ws.title = "1_Displacement_data"
        if request.GET.get('cause') == 'conflict':
            self.export_conflicts(ws, qs)
        elif request.GET.get('cause') == 'disaster':
            self.export_disasters(ws, qs)
        else:
            self.export_displacements(ws, qs)
        # Tab 2
        ws2 = wb.create_sheet('2_Context_Displacement_data')
        ws2.append([
            'ISO3',
            'Year',
            'Figure cause',
            'Figure category',
            'Description',
            'Figures',
            'Figures rounded',
        ])
        pfa_qs = PublicFigureAnalysisFilterSet(
            data=self.request.query_params,
            queryset=PublicFigureAnalysis.objects.all()
        ).qs.order_by('iso3', 'year')
        # FIXME: sort this and filter this
        for item in pfa_qs:
            ws2.append([
                item.iso3,
                item.year,
                item.figure_cause.label,
                item.figure_category.label,
                item.description,
                item.figures,
                item.figures_rounded,
            ])
        # Tab 3
        ws3 = wb.create_sheet('3_IDPs_SADD_estimates')
        ws3.append([
            'ISO3',
            'Country',
            'Year',
            'Sex',
            'Cause',
            '0-4',
            '5-11',
            '12-17',
            '18-59',
            '60+',
        ])
        idps_sadd_qs = IdpsSaddEstimateFilter(
            data=self.request.query_params,
            queryset=IdpsSaddEstimate.objects.all(),
        ).qs.order_by('iso3', 'year')
        for item in idps_sadd_qs:
            ws3.append([
                item.iso3,
                item.country_name,
                item.year,
                item.sex,
                item.cause.label,
                item.zero_to_four,
                item.five_to_eleven,
                item.twelve_to_seventeen,
                item.eighteen_to_fiftynine,
                item.sixty_plus,
            ])
        # Tab 4
        ws4 = wb.create_sheet('README')
        readme_text = [
            ['TITLE: Disasters Global Internal Displacement Database (GIDD)'],
            [''],
            ['File name: IDMC_Internal_Displacement_Conflict-Violence_Disasters'],
            [''],
            ['SOURCE: Internal Displacement monitoring Centre (IDMC)'],
            [''],

            [f'DATE EXTRACTED: {datetime.now().strftime("%B %d, %Y")}'],
            [],
            [f'LAST UPDATE: {StatusLog.last_release_date()}'],
            [],
            ['DESCRIPTION: '],
            [
                'The Internal Displacement Monitoring Centre (IDMC) continuously monitors global displacement events '
                'triggered by conflict, violence, and disasters throughout the year. By collecting and analyzing both '
                'structured and unstructured secondary data from a variety of sources—including government agencies, '
                'UN agencies, the International Federation of the Red Cross and Red Cressent , and media—IDMC ensures '
                'comprehensive coverage and high data reliability. Data is disaggregated by type of metric '
                '(internal displacements or IDPs), cause, event, location, and data reliability. Rigorous quality '
                'controls are applied to maintain accuracy. The database contains displacement figures from various '
                'countries and regions, covering conflict-induced displacement from 2009 to 2023 and disaster-induced '
                'displacement from 2008 to 2023. For detailed definitions and more robust descriptions, please visit '
                'IDMC Monitoring Tools (https://www.internal-displacement.org/monitoring-tools).'
            ],
            [''],
            ['KEY DEFINITIONS: '],
            [''],
            [
                'Internal Displacements (flows): The estimated total number of internal displacements within the '
                'reporting year. This figure may include individuals displaced multiple times.'
            ],
            [
                'Total Number of IDPs (stocks): Represents the cumulative total of Internally Displaced Persons (IDPs) '
                'at a specific location and point in time, reflecting the total population living in displacement as '
                'of the end of the reporting year.'
            ],
            [
                'USE LICENSE: This content is licensed under CC BY-NC. Detailed licensing information is available at '
                'Creative Commons License (See: https://creativecommons.org/licenses/by-nc/4.0/).'
            ],
            [''],
            ['COVERAGE: Global'],
            [''],
            ['CONTACT: info@idmc.ch'],
            [''],
        ]

        for item in readme_text:
            ws4.append(item)

        ws4.append(['DATA DESCRIPTION: 1_Displacement_data table'])
        readme_text_2 = [
            [
                'This dataset offers annually validated data on internal displacement caused by disasters, conflicts, '
                'and other situations of violence, as compiled and reported by the Internal Displacement Monitoring '
                'Centre (IDMC).'
            ],
            [''],
            ['ISO3: ISO 3166-1 alpha-3 “AB9” was assigned to the Abyei Area.'],
            ['Country / Territory: Short name of the country or territory.'],
            ['Year: The year for which displacement figures are reported.'],
            [
                'Conflict Total number of IDPs: Total number of IDPs (rounded figures at '
                'national level), as a result, of Conflict and Violence as of the end of '
                'the reporting year.'
            ],
            [
                'Conflict Total number of IDPs raw: Total number of IDPs (not rounded), as '
                'a result, of Conflict and Violence as of the end of the reporting year.'
            ],
            [
                'Conflict Internal Displacements: Total number of internal displacements '
                'reported (rounded figures at national level), as a result of Conflict and '
                'Violence over the reporting year.'
            ],
            [
                'Conflict Internal Displacements raw: Total number of internal displacements '
                'reported (not rounded), as a result of Conflict and Violence over the '
                'reporting year.'
            ],
            [
                'Disaster Internal Displacements: Total number of internal displacements reported '
                '(rounded figures at national '
                'level), as a result of disasters over the reporting year.'
            ],
            [
                'Disaster Internal Displacements raw: Total number of internal displacements reported '
                '(not rounded), as a result of disasters over the reporting year.'
            ],
            [
                'Disaster Total number of IDPs: Total number of IDPs (rounded figures at '
                'national level), as a result, of disasters as of the end of the reporting year.'
            ],
            [
                'Disaster Total number of IDPs raw: Total number of IDPs (not rounded), as a result, of disasters as of '
                'the end of the reporting year.'
            ],
        ]
        ws4.append([])
        for item in readme_text_2:
            ws4.append(item)
        ws4.append([])
        ws4.append([
            'DATA DESCRIPTION: 2_Context_Displacement_data table'
        ])
        readme_text_3 = [
            [
                'This dataset provides contextual information and analysis documented by IDMC analysts. '
                'It captures flags related to methodology, caveats, sources, and challenges identified for each '
                'metric, reporting year, and country.'
            ],
            [],
            ['ISO3: ISO 3166-1 alpha-3  "AB9" was assigned to the Abyei Area.'],
            ['Year: The year for which displacement figures are reported.'],
            [
                'figure_category_name: Type of displacement metric, this field contrains values of '
                'Internal displacements (population flows) and  IDPs  (Total number of IDPs  or population stocks)'
            ],
            [
                'description: Contains the methodology, sources description, caveats and challenges identified for the '
                'displacement figures reported'
            ],
            ['figures: total number of displacements or total number of IDPs reported.'],
            ['figures_rounded: Rounded figures'],
        ]
        ws4.append([])
        for item in readme_text_3:
            ws4.append(item)
        readme_text_4 = [
            ['ISO3: ISO 3166-1 alpha-3. The ISO3 “AB9” was assigned to the Abyei Area.'],
            ['Country: Short name of the country or territory.'],
            ['Geographical region: Geographical region'],
            ['Year: The year for which displacement figures are reported.'],
            [
                'Sex : This field contains information on Female, Male and Both Sexes categories following the United '
                'Nations Department of Economic and Social Affairs (UN DESA) classifications. '
            ],
            ['Cause: Displacement trigger.'],
            ['Age_0_4'],
            ['Age_5_11'],
            ['Age_12_17'],
            ['Age_18_59'],
            ['Age_60_plus'],
        ]
        ws4.append([])
        ws4.append([
            'DATA DESCRIPTION: 3_IDPs_SADD_estimates table'
        ])
        ws4.append([])
        ws4.append([
            'Sex and Age Disaggregated Data (SADD) for displacement associated with conflict or disasters is often '
            'scarce. One way to estimate it is to use SADD available at the national level. IDMC employs United '
            'Nations Population Estimates and Projections to break down the number of internally displaced people by '
            'sex and age. The methodology and limitations of this approach are described on IDMC’s website at: '
            'https://www.internal-displacement.org/monitoring-tools'
        ])
        ws4.append([])
        for item in readme_text_4:
            ws4.append(item)

        response = HttpResponse(content=save_virtual_workbook(wb))
        filename = 'IDMC_Internal_Displacement_Conflict-Violence_Disasters.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        response['Content-Type'] = 'application/octet-stream'
        return response


class DisaggregationViewSet(ListOnlyViewSetMixin):
    queryset = GiddFigure.objects.all()
    serializer_class = DisaggregationSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    filterset_class = DisaggregationFilterSet

    def _get_term(self, term) -> typing.Optional[str]:
        if term is None:
            return None
        return Figure.FIGURE_TERMS.get(term).label

    def _get_category(self, category) -> typing.Optional[str]:
        if category is None:
            return
        return Figure.FIGURE_CATEGORY_TYPES.get(category).label

    def _get_cause(self, cause) -> typing.Optional[str]:
        if cause is None:
            return
        return Crisis.CRISIS_TYPE.get(cause).label

    def _get_displacement_occurred(self, displacement_occurred) -> str:
        if displacement_occurred is not None:
            return DisasterViewSet.get_displacement_status([displacement_occurred])
        return ""

    def _get_unit(self, unit) -> typing.Optional[str]:
        if unit is None:
            return None
        return Figure.UNIT.get(unit).label

    def extract_event_data(
        self,
        event_code: typing.List[typing.Tuple[str]],
        event_code_type: typing.List[typing.Tuple[str]],
        event_code_iso3: typing.List[typing.Tuple[str]],
        filter_iso3: str
    ) -> str:
        event_code_components = [
            event_code,
            event_code_type,
            event_code_iso3
        ]
        transposed_components = zip(*event_code_components)

        return EXTERNAL_ARRAY_SEPARATOR.join(
            EXTERNAL_FIELD_SEPARATOR.join([loc[0], loc[1]])
            for loc in transposed_components
            if loc[2] == filter_iso3
        )

    @staticmethod
    def string_join(
        separator: str,
        data: typing.List[str],
    ) -> str:
        return separator.join([
            str(item)
            for item in data
            if item is not None
        ])

    @staticmethod
    def remove_null_from_dict(data: dict) -> dict:
        return {
            key: value
            for key, value in data.items()
            if value is not None
        }

    def _export_disaggregated_geojson(self, qs):

        def format_coordinate(coordinate: str) -> typing.Tuple[float, float]:
            lat, lng = coordinate.split(', ')
            return (float(lng), float(lat))

        def format_coordinates(coordinates: typing.List[str]):
            return [format_coordinate(x) for x in coordinates]

        qs = qs.exclude(
            Q(locations_coordinates__isnull=True) |
            Q(locations_coordinates=[])
        ).annotate(
            event_main_trigger=Case(
                When(
                    gidd_event__cause=Crisis.CRISIS_TYPE.CONFLICT,
                    then=F('gidd_event__violence__name')
                ),
                When(
                    gidd_event__cause=Crisis.CRISIS_TYPE.DISASTER,
                    then=F('gidd_event__disaster_sub_type__name')
                ),
                When(
                    gidd_event__cause=Crisis.CRISIS_TYPE.OTHER,
                    then=F('gidd_event__other_sub_type__name')
                ),
                output_field=models.CharField()
            ),
        )
        feature_collection = {
            "type": "FeatureCollection",
            "features": []
        }

        for item in qs:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "MultiPoint",
                    "coordinates": format_coordinates(item.locations_coordinates),
                },
                "properties": self.remove_null_from_dict({
                    "ID": item.figure_id,
                    "ISO3": item.iso3,
                    "Country": item.country_name,
                    "Geographical region": item.geographical_region_name,
                    "Figure cause": self._get_cause(item.cause),
                    "Year": item.year,
                    "Figure category": self._get_category(item.category),
                    "Figure term": self._get_term(item.term),
                    "Figure unit": self._get_unit(item.unit),
                    "Reported figures": item.reported,
                    "Household size": item.household_size,
                    "Total figures": item.total_figures,
                    "Hazard category": item.disaster_category_name,
                    "Hazard sub category": item.disaster_sub_category_name,
                    "Hazard type": item.disaster_type_name,
                    "Hazard sub type": item.disaster_sub_type_name,
                    "Violence type": item.violence_name,
                    "Other event sub type": item.other_sub_type_name,
                    "Start date": item.start_date,
                    "Start date accuracy": item.start_date_accuracy,
                    "End date": item.end_date,
                    "End date accuracy": item.end_date_accuracy,
                    "Stock date": item.stock_date,
                    "Stock date accuracy": item.stock_date_accuracy,
                    "Stock reporting date": item.stock_reporting_date,
                    "Publishers": item.publishers,
                    "Sources": item.sources,
                    "Sources type": item.sources_type,
                    "Event ID": item.gidd_event.event_id,
                    "Event name": item.gidd_event.name,
                    "Event cause": self._get_cause(item.gidd_event.cause),
                    "Event main trigger": item.event_main_trigger,
                    "Event start date": item.gidd_event.start_date,
                    "Event end date": item.gidd_event.end_date,
                    "Event start date accuracy": item.gidd_event.start_date_accuracy,
                    "Event end date accuracy": item.gidd_event.end_date_accuracy,
                    "Is housing destruction": "Yes" if item.is_housing_destruction is not None else "No",
                    "Event codes (Code:Type)": self.extract_event_data(
                        item.gidd_event.event_codes,
                        item.gidd_event.event_codes_type,
                        item.gidd_event.event_codes_iso3,
                        item.iso3,
                    ),
                    "Locations name": item.locations_names,
                    "Locations accuracy": item.locations_accuracy,
                    "Locations type": item.locations_type,
                    "Displacement occurred": self._get_displacement_occurred(item.displacement_occurred),
                })
            }
            feature_collection['features'].append(feature)

        feature_collection = json.dumps(feature_collection, cls=DjangoJSONEncoder)
        response = HttpResponse(content=feature_collection, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="IDMC_Internal_Displacement_Disaggregated.geojson"'
        return response

    def _export_disaggregated_excel(self, qs):
        wb = Workbook()
        ws = wb.active
        ws.title = "1_Disaggregated_Data"
        ws.append([
            'ID',
            'ISO3',
            'Country',
            'Geographical region',
            'Figure cause',
            'Year',
            'Figure category',
            'Figure term',
            'Figure unit',
            'Reported figures',
            'Household size',
            'Total figures',
            'Hazard category',
            'Hazard sub category',
            'Hazard type',
            'Hazard sub type',
            'Violence type',
            'Other event sub type',
            'Start date',
            'Start date accuracy',
            'End date',
            'End date accuracy',
            'Stock date',
            'Stock date accuracy',
            'Stock reporting date',
            'Publishers',
            'Sources',
            'Sources type',
            'Event ID',
            'Event name',
            'Event cause',
            'Event main trigger',
            'Event start date',
            'Event end date',
            'Event start date accuracy',
            'Event end date accuracy',
            'Is housing destruction',
            'Event codes (Code:Type)',
            'Locations coordinates',
            'Locations name',
            'Locations accuracy',
            'Locations type',
            'Displacement occurred',
        ])

        # Tab 2
        ws2 = wb.create_sheet('2_Context_Displacement_data')
        ws2.append([
            'ISO3',
            'Year',
            'Figure cause',
            'Figure category',
            'Description',
            'Figures',
            'Figures rounded',
        ])
        pfa_qs = PublicFigureAnalysisFilterSet(
            data=self.request.query_params,
            queryset=PublicFigureAnalysis.objects.all()
        ).qs.order_by('iso3', 'year')
        # FIXME: sort this and filter this
        for item in pfa_qs:
            ws2.append([
                item.iso3,
                item.year,
                item.figure_cause.label,
                item.figure_category.label,
                item.description,
                item.figures,
                item.figures_rounded,
            ])

        # README TAB
        ws3 = wb.create_sheet('README')
        readme_text = [
            ['TITLE: Disasters Global Internal Displacement Database (GIDD)'],
            [],
            ['FILENAME: IDMC_Internal_Displacement_Disaggregated'],
            [],
            ['SOURCE: Internal Displacement Monitoring Centre (IDMC)'],
            [],
            [f'DATE EXTRACTED: {datetime.now().strftime("%B %d, %Y")}'],
            [],
            [f'LAST UPDATE: {StatusLog.last_release_date()}'],
            [],
            ['DESCRIPTION:'],
            [
                'The Internal Displacement Monitoring Centre (IDMC) continuously monitors global displacement events '
                'triggered by conflict, violence, and disasters throughout the year. By collecting and analyzing both '
                'structured and unstructured secondary data from a variety of sources—including government agencies, '
                'UN agencies, the International Federation of the Red Cross and Red Cressent , and media—IDMC ensures '
                'comprehensive coverage and high data reliability. Data is disaggregated by type of metric '
                '(internal displacements or IDPs), cause, event, location, and data reliability. Rigorous quality '
                'controls are applied to maintain accuracy. The database contains displacement figures from various '
                'countries and regions, covering conflict-induced displacement from 2009 to 2023 and disaster-induced '
                'displacement from 2008 to 2023. For detailed definitions and more robust descriptions, please visit '
                'IDMC Monitoring Tools (https://www.internal-displacement.org/monitoring-tools).'
            ],
            [''],
            ['KEY DEFINITIONS:'],
            [''],
            [
                'Internal Displacements (flows): The estimated total number of internal displacements within the '
                'reporting year. This figure may include individuals displaced multiple times.'
            ],
            [
                'Total Number of IDPs (stocks): Represents the cumulative total of Internally Displaced Persons (IDPs) '
                'at a specific location and point in time, reflecting the total population living in displacement as '
                'of the end of the reporting year.'
            ],
            [
                'USE LICENSE: This content is licensed under CC BY-NC. Detailed licensing information is available at '
                'Creative Commons License (See: https://creativecommons.org/licenses/by-nc/4.0/).'
            ],
            [''],
            ['COVERAGE: Global'],
            [''],
            ['CONTACT: info@idmc.ch'],
        ]

        for item in readme_text:
            ws3.append(item)
        ws3.append([])
        ws3.append(['DATA DESCRIPTION: 1_Disaggregated_Data table'])
        ws3.append([])

        data_description_1 = [
            ["ID: IDMC figure unique identifier"],
            ["ISO3: ISO 3166-1 alpha-3 'AB9' was assigned to the Abyei Area."],
            ["Country / Territory: Short name of the country or territory."],
            ["Geographical region: IDMC geographical region"],
            ["Figure cause: Displacement trigger"],
            ["Year: The year for which displacement figures are reported."],
            [
                "Figure category: Type of displacement metric, this field contains values of Internal displacements "
                "(population flows) and  IDPs  (Total number of IDPs  or population stocks)"
            ],
            ["Total figures: Total value of internal displacement categories reported"],
            ["Reported: Figures can be reported in households of numbers of people."],
            ["Figure term: Reported term used by the source of the figure"],
            ["Unit: Unit of reporting. It can be households or people"],
            ["Hazard Category: Based on the CRED EM-DAT classification."],
            ["Hazard sub type: Specific sub-type of the hazard as per CRED EM-DAT."],
            ["Hazard type: Hazard type as categorized by CRED EM-DAT."],
            ["Start date: Start date of displacement flow"],
            ["Start date accuracy: Uncertainty or accuracy of start date"],
            ["End date: End date of the displacement flow"],
            ["End date accuracy: Uncertainty or accuracy of end date"],
            ["Stock date: Stock date"],
            ["Stock date accuracy: Uncertainty or accuracy of stock date"],
            [
                "Stock reporting date: This corresponds to IDMC's reporting timeframe of the total number of people "
                "leaving on situations of internal displacement."
            ],
            ["Publishers: Organizations responsible for distributing and disseminating internal displacement data"],
            ["Sources:  The original providers of data on internal displacement or primary source of data."],
            ["Sources type: IDMC's source type."],
            ["Event ID: IDMC's unique event ID"],
            [
                "Event name: Common or official event name for the event, if available. Otherwise, events are coded "
                "based on the country, type of hazard, location, and event start date."
            ],
            ["Event cause: Cause or main driver of displacement event."],
            ["Event main trigger: Event main hazard sub  type or conflict type"],
            ["Event start date: Event or hazard start date"],
            ["Event end date: Event or hazard end date date"],
            ["Event start date accuracy: Uncertainty or accuracy of event start date"],
            ["Event end date accuracy: Uncertainty or accuracy of event end date"],
            [
                "Is housing destruction: This field represents if the figure also represent the number of people "
                "displaced resulting form housing destruction. The values of this field are Yes or No to flag figures "
                "that reported housing destruction too. To calculate "
            ],
            [
                "Violence type: This field categorizes the type of violence using IDMC's typology, which aligns with "
                "international classifications. The categories include\n"
                "- International Armed Conflict (IAC): Refers to armed conflict between two or more states.\n"
                "- Non-International Armed Conflict (NIAC): Refers to protracted armed conflict occurring within the "
                "territory of a single state between its government and non-state armed groups, or between such groups "
                "themselves.\n"
                "- Unclear/Unknown: Indicates situations where the type of violence is not definitively categorized "
                "due to limited information."
            ],
            [
                "Event codes (Code:Type): Unique codes such as the GLIDE number and other database-specific codes used "
                "to identify and track specific events across various databases."
            ],
            ["Locations name: Name of locations were displacement was reported"],
            ["Locations coordinates: This field contains geographic coordinates representing the reported locations."],
            [
                "Locations accuracy:  This field indicates the estimated precision of the reported locations. It "
                "serves as a clue to the likely administrative unit level (e.g., country, state, district) used for "
                "reporting."
            ],
            [
                "Locations type: This field specifies the type of displacement location within a reported event. It "
                "can indicate, Origin: The place where people were displaced from. Destination: The location where "
                "displaced people arrived. Both: In some cases, both origin and destination information might be "
                "included."
            ],
            [
                "Displacement occurred: This refers to situations where people are moved from a potentially dangerous "
                "area as a precaution, triggered by an early warning system."
            ],
        ]
        for item in data_description_1:
            ws3.append(item)
        ws3.append([])
        ws3.append(['DATA DESCRIPTION: 2_Context_Displacement_data table'])
        ws3.append([])
        ws3.append([
            'This dataset provides contextual information and analysis documented by IDMC analysts. It captures flags '
            'related to methodology, caveats, sources, and challenges identified for each metric, reporting year, and '
            'country.'
        ])
        ws3.append([])

        data_description_2 = [
            ["ISO3: ISO 3166-1 alpha-3  'AB9' was assigned to the Abyei Area."],
            ["Year: The year for which displacement figures are reported."],
            ["figure_cause_name: Trigger of displacement"],
            [
                "figure_category_name: Type of displacement metric, this field contains values of Internal "
                "displacements (population flows) and  IDPs  (Total number of IDPs  or population stocks)"
            ],
            [
                "description: Contains the methodology, sources description, caveats and challenges identified for "
                "the displacement figures reported"
            ],
            ["figures: total number of displacements or total number of IDPs reported."],
            ["figures_rounded: Rounded figures"],
        ]
        for item in data_description_2:
            ws3.append(item)

        qs = qs.filter(
            locations_coordinates__isnull=False,
        ).annotate(
            event_main_trigger=Case(
                When(
                    gidd_event__cause=Crisis.CRISIS_TYPE.CONFLICT,
                    then=F('gidd_event__violence__name')
                ),
                When(
                    gidd_event__cause=Crisis.CRISIS_TYPE.DISASTER,
                    then=F('gidd_event__disaster_sub_type__name')
                ),
                When(
                    gidd_event__cause=Crisis.CRISIS_TYPE.OTHER,
                    then=F('gidd_event__other_sub_type__name')
                ),
                output_field=models.CharField(),
            ),
        )

        for item in qs:
            ws.append([
                item.figure_id,
                item.iso3,
                item.country_name,
                item.geographical_region_name,
                self._get_cause(item.cause),
                item.year,
                self._get_category(item.category),
                self._get_term(item.term),
                self._get_unit(item.unit),
                item.reported,
                item.household_size,
                item.total_figures,
                item.disaster_category_name,
                item.disaster_sub_category_name,
                item.disaster_type_name,
                item.disaster_sub_type_name,
                item.violence_name,
                item.other_sub_type_name,
                item.start_date,
                item.start_date_accuracy,
                item.end_date,
                item.end_date_accuracy,
                item.stock_date,
                item.stock_date_accuracy,
                item.stock_reporting_date,
                self.string_join(EXTERNAL_ARRAY_SEPARATOR, item.publishers),
                self.string_join(EXTERNAL_ARRAY_SEPARATOR, item.sources),
                self.string_join(EXTERNAL_ARRAY_SEPARATOR, item.sources_type),
                item.gidd_event.event_id,
                item.gidd_event.name,
                self._get_cause(item.gidd_event.cause),
                item.event_main_trigger,
                item.gidd_event.start_date,
                item.gidd_event.end_date,
                item.gidd_event.start_date_accuracy,
                item.gidd_event.end_date_accuracy,
                "Yes" if item.is_housing_destruction else "No",
                self.extract_event_data(
                    item.gidd_event.event_codes,
                    item.gidd_event.event_codes_type,
                    item.gidd_event.event_codes_iso3,
                    item.iso3,
                ),
                self.string_join(EXTERNAL_ARRAY_SEPARATOR, item.locations_coordinates),
                self.string_join(EXTERNAL_ARRAY_SEPARATOR, item.locations_names),
                self.string_join(EXTERNAL_ARRAY_SEPARATOR, item.locations_accuracy),
                self.string_join(EXTERNAL_ARRAY_SEPARATOR, item.locations_type),
                self._get_displacement_occurred(item.displacement_occurred),
            ])

        response = HttpResponse(content=save_virtual_workbook(wb))
        filename = 'IDMC_Internal_Displacement_Disaggregated.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        response['Content-Type'] = 'application/octet-stream'
        return response

    @extend_schema(responses=DisaggregationSerializer(many=True))
    @action(
        detail=False,
        methods=["get"],
        url_path="disaggregated-geojson",
        permission_classes=[AllowAny],
    )
    def export_disaggregated_geojson(self, request):
        """
        Export the disaggregated data in geojson format file
        """
        track_gidd(
            self.request.GET.get('client_id'),
            ExternalApiDump.ExternalApiType.GIDD_DISAGGREGATION_EXPORT_GEOJSON,
            viewset=self,
        )
        queryset = GiddFigure.objects.select_related('gidd_event').order_by(
            '-year',
            'iso3',
            'id',
        )
        qs = self.filter_queryset(queryset)
        return self._export_disaggregated_geojson(qs)

    @extend_schema(responses=DisaggregationSerializer(many=True))
    @action(
        detail=False,
        methods=["get"],
        url_path="disaggregated-export",
        permission_classes=[AllowAny],
    )
    def export_disaggregated(self, request):
        """
        Export the disaggregated data in excel format file
        """
        track_gidd(
            self.request.GET.get('client_id'),
            ExternalApiDump.ExternalApiType.GIDD_DISAGGREGATION_EXPORT_EXCEL,
            viewset=self,
        )
        queryset = GiddFigure.objects.select_related('gidd_event').order_by(
            '-year',
            'iso3',
            'id',
        )
        qs = self.filter_queryset(queryset)
        return self._export_disaggregated_excel(qs)


class PublicFigureAnalysisViewSet(ListOnlyViewSetMixin):
    serializer_class = PublicFigureAnalysisSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    filterset_class = PublicFigureAnalysisFilterSet

    def get_queryset(self):
        track_gidd(
            self.request.GET.get('client_id'),
            ExternalApiDump.ExternalApiType.GIDD_PUBLIC_FIGURE_ANALYSIS_REST,
            viewset=self,
        )
        return PublicFigureAnalysis.objects.all()
