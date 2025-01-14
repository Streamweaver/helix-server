import typing


REDIS_SEPARATOR = ':'
INTERNAL_SEPARATOR = ':'

EXTERNAL_TUPLE_SEPARATOR = ', '
EXTERNAL_ARRAY_SEPARATOR = '; '
EXTERNAL_FIELD_SEPARATOR = ':'


def format_locations(
    locations_data: typing.List[typing.Tuple[str, str, str, str]]
) -> typing.List[typing.Tuple[str, str, str, str]]:
    """
    Format the locations data by converting raw accuracy and type of point values to their corresponding labels.

    This function takes a list of tuples representing location data and returns a formatted list where the
    accuracy and type of point values are replaced with their respective labels.

    :param locations_data: A list of tuples representing location data. Each tuple contains:
                           (location_name, location, accuracy, type_of_point)
    :type locations_data: List[Tuple[str, str, str, str]]

    :return: A formatted list of tuples containing:
             (location_name, location, accuracy_label, type_of_point_label)
    :rtype: List[Tuple[str, str, str, str]]

    Accuracy values and their corresponding labels:
    0: Country/territory (ADM0)
    1: State/Region/Province (ADM1)
    2: District/Zone/Department (ADM2)
    3: County/City/town/Village/Woreda (ADM3)
    4: Point

    Type of point values and their corresponding labels:
    0: Origin
    1: Destination
    2: Origin and destination

    Example usage:
    ```
    raw_locations = [
        ('United States', 'Washington D.C.', '0', '0'),
        ('California', 'Sacramento', '1', '1'),
        ('Los Angeles County', 'Los Angeles', '2', '2'),
        ('San Francisco', 'Golden Gate Bridge', '3', '0'),
        ('Yosemite National Park', 'Half Dome', '4', '1'),
    ]
    formatted_locations = format_locations(raw_locations)
    print(formatted_locations)
    ```

    Expected output:
    ```
    [
        ('United States', 'Washington D.C.', 'Country/territory (ADM0)', 'Origin'),
        ('California', 'Sacramento', 'State/Region/Province (ADM1)', 'Destination'),
        ('Los Angeles County', 'Los Angeles', 'District/Zone/Department (ADM2)', 'Origin and destination'),
        ('San Francisco', 'Golden Gate Bridge', 'County/City/town/Village/Woreda (ADM3)', 'Origin'),
        ('Yosemite National Park', 'Half Dome', 'Point', 'Destination')
    ]
    ```

    Note: The actual labels are retrieved using the OSMName.OSM_ACCURACY and OSMName.IDENTIFIER enums.
    """
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
            _get_identifier_label(type_of_point),
        ])
    return location_list


def format_locations_raw(
    locations_data: typing.List[typing.Tuple[str, str, str, str, str]]
) -> typing.List[typing.Tuple[int, str, str, int, int]]:
    """
    Format raw locations data.

    This method takes a list of tuples as input, where each tuple represents a raw location data. Each tuple contains 5
    elements in the following order: location_id (str), location_name (str), location (str), accuracy (str), and
    type_of_point (str).

    The method iterates over each tuple and extracts the required elements. It converts `location_id`, `accuracy`, and
    `type_of_point` to integers and strips leading and trailing spaces from `location_name`. The transformed elements
    are then appended to a new list.

    The method returns a list of tuples, where each tuple represents a formatted location. Each tuple contains 5
    elements in the following order: formatted_location_id (int), formatted_location_name (str), location (str),
    formatted_accuracy (int), and formatted_type_of_point (int).

    Accuracy values:
    0: Country/territory (ADM0)
    1: State/Region/Province (ADM1)
    2: District/Zone/Department (ADM2)
    3: County/City/town/Village/Woreda (ADM3)
    4: Point

    Type of point values:
    0: Origin
    1: Destination
    2: Origin and destination

    Example usage:
    ```
    raw_locations = [
        ('1', 'United States', 'Washington D.C.', '0', '0'),
        ('2', 'California', 'Sacramento', '1', '1'),
        ('3', 'Los Angeles County', 'Los Angeles', '2', '2'),
        ('4', 'San Francisco', 'Golden Gate Bridge', '3', '0'),
        ('5', 'Yosemite National Park', 'Half Dome', '4', '1'),
    ]
    formatted_locations = format_locations_raw(raw_locations)
    print(formatted_locations)
    ```

    Output:
    ```
    [
        (1, 'United States', 'Washington D.C.', 0, 0),
        (2, 'California', 'Sacramento', 1, 1),
        (3, 'Los Angeles County', 'Los Angeles', 2, 2),
        (4, 'San Francisco', 'Golden Gate Bridge', 3, 0),
        (5, 'Yosemite National Park', 'Half Dome', 4, 1)
    ]
    ```
    """
    location_list = []
    for loc in locations_data:
        location_id, location_name, location, accuracy, type_of_point = loc
        location_list.append([
            int(location_id),
            location_name.strip(),
            location,
            int(accuracy),
            int(type_of_point),
        ])
    return location_list


def format_locations_as_string(
    locations_data: typing.List[typing.Tuple[str, str, str, str]],
) -> str:
    """
    Format locations data as a string, converting raw values to labels.

    This function takes a list of tuples representing location data, formats it
    using the format_locations function, and joins the formatted data into a
    single string.

    Args:
        locations_data: A list of tuples representing location data. Each tuple
                        should have four string elements:
                        (location_name, location, accuracy, type_of_point)

    Returns:
        A formatted string representing the locations data, with each location's
        data separated by EXTERNAL_ARRAY_SEPARATOR and each field within a
        location separated by EXTERNAL_FIELD_SEPARATOR.

    Accuracy values and their corresponding labels:
        0: Country/territory (ADM0)
        1: State/Region/Province (ADM1)
        2: District/Zone/Department (ADM2)
        3: County/City/town/Village/Woreda (ADM3)
        4: Point

    Type of point values and their corresponding labels:
        0: Origin
        1: Destination
        2: Origin and destination

    Example:
        >>> locations_data = [
        ...     ('United States', 'Washington D.C.', '0', '0'),
        ...     ('California', 'Sacramento', '1', '1')
        ... ]
        >>> format_locations_as_string(locations_data)
        'United States,Washington D.C.,Country/territory (ADM0),
        Origin;California,Sacramento,State/Region/Province (ADM1),Destination'

    Note:
        The actual separator values (EXTERNAL_ARRAY_SEPARATOR and
        EXTERNAL_FIELD_SEPARATOR) depends on the input.
        The example uses ';' and ',' for illustration purposes.
    """
    return EXTERNAL_ARRAY_SEPARATOR.join(
        EXTERNAL_FIELD_SEPARATOR.join(loc)
        for loc in format_locations(locations_data)
    )


class ExtractLocationData(typing.TypedDict):
    """
    ExtractLocationData is a typed dictionary class that represents location data.

    Attributes:
        display_name (List[str]): A list of display names for the location.
        lat_lon (List[str]): A list of latitude and longitude coordinates for the location.
        accuracy (List[str]): A list of accuracy values for the location. Valid values are:
            '0': Country/territory (ADM0)
            '1': State/Region/Province (ADM1)
            '2': District/Zone/Department (ADM2)
            '3': County/City/town/Village/Woreda (ADM3)
            '4': Point
        type_of_points (List[str]): A list of the type of points for the location. Valid values are:
            '0': Origin
            '1': Destination
            '2': Origin and destination

    Example:
        {
            'display_name': ['United States', 'California', 'Los Angeles'],
            'lat_lon': ['34.0522', '-118.2437'],
            'accuracy': ['0', '1', '3'],
            'type_of_points': ['0', '1', '2']
        }

    Note:
        The actual labels for accuracy and type_of_points are typically retrieved using
        OSMName.OSM_ACCURACY and OSMName.IDENTIFIER enums respectively.
    """
    display_name: typing.List[str]
    lat_lon: typing.List[str]
    accuracy: typing.List[str]
    type_of_points: typing.List[str]


class ExtractLocationDataRaw(typing.TypedDict):
    """
    This class represents the raw data extracted for location data.

    Attributes:
        ids (List[str]): A list of IDs associated with the locations.
        display_name (List[str]): A list of display names for the locations.
        lat_lon (List[str]): A list of latitude-longitude pairs for the locations.
        accuracy (List[int]): A list of accuracy values for the locations.
        type_of_points (List[int]): A list of type of points for the locations.

    """
    ids: typing.List[str]
    display_name: typing.List[str]
    lat_lon: typing.List[str]
    accuracy: typing.List[int]
    type_of_points: typing.List[int]


class ExtractLocationDataAsString(typing.TypedDict):
    """
    ExtractLocationDataAsString

    A class representing location data extracted as strings.

    Attributes:
        display_name (str): The display name of the location.
        lat_lon (str): The latitude and longitude of the location.
        accuracy (str): The accuracy of the location data.
        type_of_points (str): The type of points used in the location data.
    """
    display_name: str
    lat_lon: str
    accuracy: str
    type_of_points: str


def extract_location_data_list(
    data: typing.List[typing.Tuple[str, str, str, str]],
) -> ExtractLocationData:
    """
    Extracts the location data from a list of tuples and returns a dictionary.

    Parameters:
        data (List[Tuple[str, str, str, str]]): A list of tuples containing formatted location data. Each tuple should
        have four elements representing display name, latitude and longitude, accuracy, and type of points.

    Returns:
        ExtractLocationData: A dictionary containing the extracted location data. The dictionary has four keys:
        'display_name', 'lat_lon', 'accuracy', and 'type_of_points'. The corresponding values are lists that contain the
        extracted data from the input tuples.

    Accuracy values:
        '0': Country/territory (ADM0)
        '1': State/Region/Province (ADM1)
        '2': District/Zone/Department (ADM2)
        '3': County/City/town/Village/Woreda (ADM3)
        '4': Point

    Type of points values:
        '0': Origin
        '1': Destination
        '2': Origin and destination

    Example:
        data = [
            ('United States', '38.8951,-77.0364', '0', '0'),
            ('California', '36.7783,-119.4179', '1', '1'),
            ('Los Angeles', '34.0522,-118.2437', '3', '2')
        ]
        result = extract_location_data_list(data)
        print(result)
        # Output:
        # {
        #     'display_name': ['United States', 'California', 'Los Angeles'],
        #     'lat_lon': ['38.8951,-77.0364', '36.7783,-119.4179', '34.0522,-118.2437'],
        #     'accuracy': ['0', '1', '3'],
        #     'type_of_points': ['0', '1', '2']
        # }

    Note:
        The actual labels for accuracy and type_of_points are typically retrieved using
        OSMName.OSM_ACCURACY and OSMName.IDENTIFIER enums respectively in the application.
    """
    # Split the formatted location data into individual components
    location_components = format_locations(data)

    transposed_components = zip(*location_components)

    return {
        'display_name': next(transposed_components, []),
        'lat_lon': next(transposed_components, []),
        'accuracy': next(transposed_components, []),
        'type_of_points': next(transposed_components, [])
    }


def extract_location_raw_data_list(
    data: typing.List[typing.Tuple[str, str, str, str, str]],
) -> ExtractLocationDataRaw:
    """
    Extracts location raw data from a list of tuples and returns a dictionary

    :param data: A list of tuples containing the location data.
                 Each tuple represents a row of data with the following
                 components:
                 - ID (string)
                 - Display Name (string)
                 - Latitude and Longitude (string)
                 - Accuracy (string)
                 - Type of Points (string)

    :return: A dictionary containing the extracted location data with the following keys:
             - 'ids': A list of IDs extracted from the data.
             - 'display_name': A list of display names extracted from the data.
             - 'lat_lon': A list of latitude and longitude values extracted from the data.
             - 'accuracy': A list of accuracy values extracted from the data.
             - 'type_of_points': A list of type of points values extracted from the data.
    """
    # Split the formatted location data into individual components
    location_components = format_locations_raw(data)

    transposed_components = zip(*location_components)

    return {
        'ids': next(transposed_components, []),
        'display_name': next(transposed_components, []),
        'lat_lon': next(transposed_components, []),
        'accuracy': next(transposed_components, []),
        'type_of_points': next(transposed_components, [])
    }


def extract_location_data(
    data: typing.List[typing.Tuple[str, str, str, str]],
) -> ExtractLocationDataAsString:
    """
    Extracts location data from a list and returns the extracted data as a string.

    Parameters:
        data (List[Tuple[str, str, str, str]]): A list of tuples containing location data. Each tuple should have four
        elements in the order of display name, lat-lon, accuracy, and type of points.

    Returns:
        Dict[str, str]: A dictionary containing the extracted location data as strings.
            The dictionary has the following keys:
            'display_name': A string representing the joined display names of the locations.
            'lat_lon': A string representing the joined lat-lon values of the locations.
            'accuracy': A string representing the joined accuracy values of the locations.
            'type_of_points': A string representing the joined type of points values of the locations.

    Accuracy values:
        '0': Country/territory (ADM0)
        '1': State/Region/Province (ADM1)
        '2': District/Zone/Department (ADM2)
        '3': County/City/town/Village/Woreda (ADM3)
        '4': Point

    Type of points values:
        '0': Origin
        '1': Destination
        '2': Origin and destination

    Example Usage:
        >>> data = [
        ...     ('United States', '38.8951,-77.0364', '0', '0'),
        ...     ('California', '36.7783,-119.4179', '1', '1'),
        ...     ('Los Angeles', '34.0522,-118.2437', '3', '2'),
        ... ]
        >>> extract_location_data(data)
        {'display_name': 'United States,California,Los Angeles',
        'lat_lon': '38.8951,-77.0364,36.7783,-119.4179,34.0522,-118.2437',
        'accuracy': '0,1,3',
        'type_of_points': '0,1,2'}

    Note:
        The actual labels for accuracy and type_of_points are typically retrieved using
        OSMName.OSM_ACCURACY and OSMName.IDENTIFIER enums respectively.
        The returned strings use EXTERNAL_FIELD_SEPARATOR to join the values.
    """
    location_components = extract_location_data_list(data)

    return {
        'display_name': EXTERNAL_ARRAY_SEPARATOR.join(location_components['display_name']),
        'lat_lon': EXTERNAL_ARRAY_SEPARATOR.join(location_components['lat_lon']),
        'accuracy': EXTERNAL_ARRAY_SEPARATOR.join(location_components['accuracy']),
        'type_of_points': EXTERNAL_ARRAY_SEPARATOR.join(location_components['type_of_points'])
    }


def format_event_codes(
    event_codes_data: typing.List[typing.Union[typing.Tuple[str, str, str], typing.Tuple[str, str]]]
) -> typing.List[typing.Union[typing.Tuple[str, str, str], typing.Tuple[str, str]]]:
    """
    Formats event codes by retrieving the label for each event code type.

    :param event_codes_data: A list of tuples representing event codes.
        Each tuple can have either 2 or 3 elements:
        - If the tuple has 3 elements: (event_code, event_code_type, event_iso3)
        - If the tuple has 2 elements: (event_code, event_code_type)
        The event_code_type is a string value between '1' and '5', representing:
        1: Glide Number
        2: Government Assigned Identifier
        3: IFRC Appeal ID
        4: ACLED ID
        5: Local Identifier

    :return: A list of tuples representing formatted event codes.
        Each tuple will have the same number of elements as the input tuple:
        - If the input tuple had 3 elements: (event_code, event_code_label, event_iso3)
        - If the input tuple had 2 elements: (event_code, event_code_label)
        The event_code_label is the string representation of the event code type.

    :raises ValueError: If an invalid event_code_type is provided.
    """
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


def format_event_codes_raw(
    event_codes_data: typing.List[typing.Tuple[str, str, str, str]]
) -> typing.List[typing.Tuple[int, str, int, str]]:
    """
    Formats the raw event codes data into a list of tuples with specific data types.

    Args:
        event_codes_data (List[Tuple[str, str, str, str]]): A list of tuples representing the raw event codes data.
            Each tuple contains four strings:
            - _id: A unique identifier for the event code.
            - event_code: The actual event code.
            - event_code_type: A string value between '1' and '5', representing:
              1: Glide Number
              2: Government Assigned Identifier
              3: IFRC Appeal ID
              4: ACLED ID
              5: Local Identifier
            - event_iso3: The ISO3 code for the event's location.

    Returns:
        List[Tuple[int, str, int, str]]: The formatted event codes data as a list of tuples.
            Each tuple contains four elements:
            - _id as int: The unique identifier converted to an integer.
            - event_code as str: The event code string.
            - event_code_type as int: The event code type converted to an integer (1-5).
            - event_iso3 as str: The ISO3 code string.

    Note:
        Tuples with None as _id are skipped in the output.
    """
    code_list = []
    for code in event_codes_data:
        _id, event_code, event_code_type, event_iso3 = code
        if _id is None:
            continue
        code_list.append([
            int(_id),
            event_code,
            int(event_code_type),
            event_iso3,
        ])
    return code_list


def format_event_codes_as_string(
    event_codes_data: typing.List[typing.Union[typing.Tuple[str, str, str], typing.Tuple[str, str]]]
) -> str:
    """
    Formats event codes data as a string.

    Args:
        event_codes_data (List[Union[Tuple[str, str, str], Tuple[str, str]]]):
            A list of tuples representing event codes data. Each tuple can have either 2 or 3 elements:
            - If the tuple has 3 elements: (event_code, event_code_type, event_iso3)
            - If the tuple has 2 elements: (event_code, event_code_type)
            The event_code_type is a string value between '1' and '5', representing:
            1: Glide Number
            2: Government Assigned Identifier
            3: IFRC Appeal ID
            4: ACLED ID
            5: Local Identifier

    Returns:
        str: A string representation of the formatted event codes data.
             The format is "event_code:event_code_label[:event_iso3]" for each tuple,
             separated by EXTERNAL_ARRAY_SEPARATOR.

    Note:
        This function internally calls format_event_codes() to convert event_code_type
        to its corresponding label before formatting as a string.

    Example usage:
        event_codes_data = [
            ("001", "1", "USA"),
            ("002", "2"),
            ("003", "3", "GBR")
        ]
        formatted_data = format_event_codes_as_string(event_codes_data)
        print(formatted_data)
        # Output might be: "001:Glide Number:USA,002:Government Assigned Identifier,003:IFRC Appeal ID:GBR"
        # (actual output depends on EXTERNAL_ARRAY_SEPARATOR and EXTERNAL_FIELD_SEPARATOR values)

    """
    return EXTERNAL_ARRAY_SEPARATOR.join(
        EXTERNAL_FIELD_SEPARATOR.join(loc)
        for loc in format_event_codes(event_codes_data)
    )


def extract_event_code_data_list(
    data: typing.List[typing.Union[typing.Tuple[str, str, str], typing.Tuple[str, str]]]
):
    """
    Extracts event code data from a given list of tuples.

    Parameters:
    - data (List[Union[Tuple[str, str, str], Tuple[str, str]]]): The input data containing event code information.
      Each tuple can have either 2 or 3 elements:
      - If the tuple has 3 elements: (event_code, event_code_type, event_iso3)
      - If the tuple has 2 elements: (event_code, event_code_type)
      The event_code_type is a string value between '1' and '5', representing:
      1: Glide Number
      2: Government Assigned Identifier
      3: IFRC Appeal ID
      4: ACLED ID
      5: Local Identifier

    Returns:
        A dictionary with the following keys:
        - 'code' (List[str]): A list of event codes extracted from the input data.
        - 'code_type' (List[str]): A list of event code type labels extracted from the input data.
        - 'iso3' (List[str]): A list of ISO3 country codes extracted from the input data (if provided).

    Note:
        - This function internally uses format_event_codes() to convert event_code_type to its corresponding label.
        - For tuples without an ISO3 code, an empty string will be used in the 'iso3' list.

    Example usage:
        data = [
            ('E001', '1', 'USA'),
            ('E002', '2'),
            ('E003', '3', 'IND'),
        ]
        extracted_data = extract_event_code_data_list(data)

        print(extracted_data['code'])         # Output: ['E001', 'E002', 'E003']
        print(extracted_data['code_type'])    # Output: ['Glide Number', 'Government Assigned Identifier', 'IFRC Appeal ID']
        print(extracted_data['iso3'])         # Output: ['USA', '', 'IND']
    """
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
    """
    Extracts event code data from a given list of tuples and joins each component into strings.

    Parameters:
    - data (List[Union[Tuple[str, str, str], Tuple[str, str]]]): The input data containing event code information.
      Each tuple can have either 2 or 3 elements:
      - If the tuple has 3 elements: (event_code, event_code_type, event_iso3)
      - If the tuple has 2 elements: (event_code, event_code_type)
      The event_code_type is a string value between '1' and '5', representing:
      1: Glide Number
      2: Government Assigned Identifier
      3: IFRC Appeal ID
      4: ACLED ID
      5: Local Identifier

    Returns:
        A dictionary with the following keys:
        - 'code' (str): A string of event codes joined by EXTERNAL_ARRAY_SEPARATOR.
        - 'code_type' (str): A string of event code type labels joined by EXTERNAL_ARRAY_SEPARATOR.
        - 'iso3' (str): A string of ISO3 country codes joined by EXTERNAL_ARRAY_SEPARATOR.

    Note:
        - This function internally uses extract_event_code_data_list() to process the input data.
        - The event_code_type values are converted to their corresponding labels.
        - For tuples without an ISO3 code, an empty string will be used in the 'iso3' string.

    Example usage:
        data = [
            ('E001', '1', 'USA'),
            ('E002', '2'),
            ('E003', '3', 'IND'),
        ]
        extracted_data = extract_event_code_data(data)

        # Assuming EXTERNAL_ARRAY_SEPARATOR is ','
        print(extracted_data['code'])         # Output: 'E001,E002,E003'
        print(extracted_data['code_type'])    # Output: 'Glide Number,Government Assigned Identifier,IFRC Appeal ID'
        print(extracted_data['iso3'])         # Output: 'USA,,IND'
    """
    # Split the formatted event code data into individual components
    extracted_data = extract_event_code_data_list(data)

    return {
        'code': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('code', [])),
        'code_type': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('code_type', [])),
        'iso3': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('iso3', [])),
    }


def extract_event_code_data_raw_list(
    data: typing.List[typing.Tuple[str, str, str, str]]
):
    """
    Extracts the event code data from a formatted list.

    Parameters:
        data (List[Tuple[str, str, str, str]]): The formatted event code data.

    Returns:
        dict: A dictionary containing the extracted event code data, with keys 'id', 'code', 'code_type', and 'iso3'.

    Examples:
        >>> data = [
        ...     ('1', 'EVT001', 'TYPE1', 'ISO1'),
        ...     ('2', 'EVT002', 'TYPE2', 'ISO2'),
        ... ]
        >>> extract_event_code_data_raw_list(data)
        {'id': ['1', '2'], 'code': ['EVT001', 'EVT002'], 'code_type': ['TYPE1', 'TYPE2'], 'iso3': ['ISO1', 'ISO2']}
    """
    # Split the formatted event code data into individual components
    event_code_components = format_event_codes_raw(data)

    transposed_components = zip(*event_code_components)

    return {
        'id': next(transposed_components, []),
        'code': next(transposed_components, []),
        'code_type': next(transposed_components, []),
        'iso3': next(transposed_components, []),
    }


def extract_event_code_data_raw(
    data: typing.List[typing.Tuple[str, str, str, str]]
):
    """
    Extracts specific components from raw event code data and joins each component into strings.

    Args:
        data (List[Tuple[str, str, str, str]]): List of tuples containing raw event code data.
            Each tuple should contain four elements in the following order:
            (_id, event_code, event_code_type, event_iso3)

            The event_code_type is a string value between '1' and '5', representing:
            1: Glide Number
            2: Government Assigned Identifier
            3: IFRC Appeal ID
            4: ACLED ID
            5: Local Identifier

    Returns:
        Dict[str, str]: Dictionary with extracted components, where each value is a string
        of elements joined by EXTERNAL_ARRAY_SEPARATOR. The dictionary contains:
        - 'id': String of _id values.
        - 'code': String of event_code values.
        - 'code_type': String of event_code_type values (not converted to labels).
        - 'iso3': String of event_iso3 values.

    Note:
        - This function internally uses extract_event_code_data_raw_list() to process the input data.
        - Unlike some other functions, this one does not convert event_code_type to labels.
        - EXTERNAL_ARRAY_SEPARATOR is used to join the elements of each component.

    Example usage:
        data = [
            ('1', 'E001', '1', 'USA'),
            ('2', 'E002', '2', 'GBR'),
            ('3', 'E003', '3', 'IND'),
        ]
        extracted_data = extract_event_code_data_raw(data)

        # Assuming EXTERNAL_ARRAY_SEPARATOR is ','
        print(extracted_data['id'])           # Output: '1,2,3'
        print(extracted_data['code'])         # Output: 'E001,E002,E003'
        print(extracted_data['code_type'])    # Output: '1,2,3'
        print(extracted_data['iso3'])         # Output: 'USA,GBR,IND'
    """
    # Split the formatted event code data into individual components
    extracted_data = extract_event_code_data_raw_list(data)

    return {
        'id': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('id', [])),
        'code': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('code', [])),
        'code_type': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('code_type', [])),
        'iso3': EXTERNAL_ARRAY_SEPARATOR.join(extracted_data.get('iso3', [])),
    }


class ExtractSourceData(typing.TypedDict):
    """

    This class represents the data needed to extract source data.

    Attributes:
    - ids (List[int]): A list of IDs of the data sources to extract.
    - sources (List[str]): A list of source names to extract data from.
    - sources_type (List[str]): A list of source types to extract data from.

    """
    ids: typing.List[int]
    sources: typing.List[str]
    sources_type: typing.List[str]


def extract_source_data(
        data: typing.List[typing.Tuple[str, str, str]]
) -> ExtractSourceData:
    """

    Extracts source data from a list of tuples.

    Args:
        data (List[Tuple[str, str, str]]): A list of tuples containing source data. Each tuple should have three
        elements:
            - str: The ID of the source data. If the ID is None, it will be skipped.
            - str: The source value.
            - str: The source type.

    Returns:
        Dict[str, List[Union[int, str]]]: A dictionary containing the extracted source data.
            - 'ids' (List[int]): A list of IDs of the source data.
            - 'sources' (List[str]): A list of source values.
            - 'sources_type' (List[str]): A list of source types.

    """
    ids = []
    sources = []
    sources_type = []
    for _id, source, source_type in data:
        if _id is None:
            continue
        ids.append(int(_id))
        sources.append(source)
        sources_type.append(source_type)
    return {
        'ids': ids,
        'sources': sources,
        'sources_type': sources_type,
    }


def extract_source_data_as_string(
    data: typing.List[typing.Tuple[str, str]]
) -> str:
    """
    Extracts source data and returns it as a formatted string.

    Parameters:
    - data (List[Tuple[str, str]]): A list of tuples containing source data. Each tuple should have two elements,
    representing the field name and its value.

    Returns:
    - str: A formatted string representing the source data.

    Example usage:
    data = [
        ("Field1", "Value1"),
        ("Field2", "Value2"),
        ("Field3", "Value3")
    ]

    result = extract_source_data_as_string(data)
    print(result)
    # Output: "Field1=Value1|Field2=Value2|Field3=Value3"
    """
    return EXTERNAL_ARRAY_SEPARATOR.join(
        EXTERNAL_FIELD_SEPARATOR.join(item)
        for item in data
    )


class ExtractPublisherData(typing.TypedDict):
    """
    Class: ExtractPublisherData

    This class represents a data structure used to store publisher data. It consists of the following attributes:

    - ids: A list of integers representing the unique IDs of the publishers.
    - publishers: A list of strings representing the names of the publishers.
    - publishers_type: A list of strings representing the types of the publishers.

    Example usage:
    data = ExtractPublisherData(ids=[1, 2, 3], publishers=["Publisher A", "Publisher B", "Publisher C"],
    publishers_type=["Type A", "Type B", "Type C"])

    data.ids # [1, 2, 3]
    data.publishers # ["Publisher A", "Publisher B", "Publisher C"]
    data.publishers_type # ["Type A", "Type B", "Type C"]

    Please note that this class is a data structure and does not contain any methods or functionality other than storing
    and accessing the data.
    """
    ids: typing.List[int]
    publishers: typing.List[str]
    publishers_type: typing.List[str]


def extract_publisher_data(
        data: typing.List[typing.Tuple[str, str, str]]
) -> ExtractPublisherData:
    """
    Extracts data from a list of tuples and returns a dictionary with extracted data.

    Parameters:
    - data (List[Tuple[str, str, str]]): A list of tuples containing data to be extracted. Each tuple must have three
    elements, where the first element is an ID, the second element is the publisher, and the third element is the
    publisher type.

    Returns:
    - ExtractPublisherData: A dictionary containing the extracted data. The dictionary has three keys: 'ids',
    'publishers', and 'publishers_type'. Each key corresponds to a list of the extracted data.

    Example:

    data = [
        ('123', 'Publisher 1', 'Type 1'),
        ('456', 'Publisher 2', 'Type 2'),
        (None, 'Publisher 3', 'Type 3'),
    ]

    extracted_data = extract_publisher_data(data)
    print(extracted_data)

    Output:
    {
        'ids': [123, 456],
        'publishers': ['Publisher 1', 'Publisher 2'],
        'publishers_type': ['Type 1', 'Type 2']
    }

    """
    ids = []
    publishers = []
    publishers_type = []
    for _id, publisher, publisher_type in data:
        if _id is None:
            continue
        ids.append(int(_id))
        publishers.append(publisher)
        publishers_type.append(publisher_type)
    return {
        'ids': ids,
        'publishers': publishers,
        'publishers_type': publishers_type,
    }


def extract_context_of_voilence_raw_data_list(
    data: typing.List[typing.Tuple[str, str]]
):
    """

    Extracts the context of violence from a raw data list.

    Parameters:
        data (List[Tuple[str, str]]): A list of tuples containing the ID and violence.

    Returns:
        Dict[str, List[Union[int, str]]]: A dictionary containing the extracted IDs and context of violence.

    """
    ids = []
    context_of_violence = []
    for _id, violence in data:
        if _id is None:
            continue
        ids.append(int(_id))
        context_of_violence.append(violence)
    return {
        'ids': ids,
        'context_of_violence': context_of_violence,
    }


def extract_tag_raw_data_list(
    data: typing.List[typing.Tuple[str, str]]
):
    """

    Extracts the ids and tags from a list of tuples containing raw tag data.

    Parameters:
    - data: A list of tuples containing raw tag data. Each tuple should contain an id value and a tag value.

    Returns:
    A dictionary with two keys:
    - 'ids': A list of integer id values extracted from the data.
    - 'tags': A list of tag values extracted from the data.

    """
    ids = []
    tags = []
    for _id, tag in data:
        if _id is None:
            continue
        ids.append(int(_id))
        tags.append(tag)
    return {
        'ids': ids,
        'tags': tags,
    }
