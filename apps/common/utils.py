import typing


REDIS_SEPARATOR = ':'
INTERNAL_SEPARATOR = ':'

EXTERNAL_TUPLE_SEPARATOR = ', '
EXTERNAL_ARRAY_SEPARATOR = '; '
EXTERNAL_FIELD_SEPARATOR = ':'


def format_locations(
    locations_data: typing.List[typing.Tuple[str, str, str, str]]
) -> typing.List[typing.Tuple[str, str, str, str]]:
    from apps.entry.models import OSMName

    def _get_accuracy_label(key: str) -> str:
        obj = OSMName.OSM_ACCURACY(int(key))
        return getattr(obj, "label", key)

    def _get_identifier_label(key: str) -> str:
        obj = OSMName.IDENTIFIER(int(key))
        return getattr(obj, "label", key)

    location_list = []
    for loc in locations_data:
        location_name, location, accuracy, type_of_point = loc
        location_list.append([
            location_name.strip(),
            location,
            _get_accuracy_label(accuracy),
            _get_identifier_label(type_of_point)
        ])
    return location_list


def format_locations_as_string(
    locations_data: typing.List[typing.Tuple[str, str, str, str]],
) -> str:
    return EXTERNAL_ARRAY_SEPARATOR.join(
        EXTERNAL_FIELD_SEPARATOR.join(loc)
        for loc in format_locations(locations_data)
    )


def extract_location_data(
    data: typing.List[typing.Tuple[str, str, str, str]],
):
    # Split the formatted location data into individual components
    location_components = format_locations(data)

    transposed_components = zip(*location_components)

    return {
        'display_name': EXTERNAL_ARRAY_SEPARATOR.join(next(transposed_components, [])),
        'lat_lon': EXTERNAL_ARRAY_SEPARATOR.join(next(transposed_components, [])),
        'accuracy': EXTERNAL_ARRAY_SEPARATOR.join(next(transposed_components, [])),
        'type_of_points': EXTERNAL_ARRAY_SEPARATOR.join(next(transposed_components, []))
    }


def format_event_codes(
    event_codes_data: typing.List[typing.Union[typing.Tuple[str, str, str], typing.Tuple[str, str]]]
) -> typing.List[typing.Union[typing.Tuple[str, str, str], typing.Tuple[str, str]]]:
    from apps.event.models import EventCode

    def _get_event_code_label(key: str) -> str:
        obj = EventCode.EVENT_CODE_TYPE(int(key))
        return getattr(obj, "label", key)

    code_list = []
    for code in event_codes_data:
        if len(code) == 3:
            event_code, event_code_type, event_iso3 = code
            if not event_code and not event_code_type and not event_iso3:
                continue
            code_list.append([
                event_code,
                _get_event_code_label(event_code_type),
                event_iso3,
            ])
        else:
            event_code, event_code_type = code
            if not event_code and not event_code_type:
                continue
            code_list.append([
                event_code,
                _get_event_code_label(event_code_type),
            ])

    return code_list


def format_event_codes_as_string(
    event_codes_data: typing.List[typing.Union[typing.Tuple[str, str, str], typing.Tuple[str, str]]]
) -> str:
    return EXTERNAL_ARRAY_SEPARATOR.join(
        EXTERNAL_FIELD_SEPARATOR.join(loc)
        for loc in format_event_codes(event_codes_data)
    )


def extract_event_code_data_list(
    data: typing.List[typing.Union[typing.Tuple[str, str, str], typing.Tuple[str, str]]]
):
    # Split the formatted event code data into individual components
    event_code_components = format_event_codes(data)

    transposed_components = zip(*event_code_components)

    return {
        'code': next(transposed_components, []),
        'code_type': next(transposed_components, []),
        'iso3': next(transposed_components, []),
    }


def extract_event_code_data(
    data: typing.List[typing.Union[typing.Tuple[str, str, str], typing.Tuple[str, str]]]
):
    # Split the formatted event code data into individual components
    extracted_data = extract_event_code_data_list(data)

    return {
        'code': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('code', [])),
        'code_type': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('code_type', [])),
        'iso3': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('iso3', [])),
    }
