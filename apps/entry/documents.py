read_me_data_raw = [
    ("ID", "Unique identifier"),
    ("Old ID", "Legacy ID from Helix 1.0"),
    ("Created at", "Data of creation of the figure"),
    ("Updated at", "Data of update of the figure"),
    ("ISO3", "ISO 3166-1 alpha-3. The ISO3 “AB9” was assigned to the Abyei Area"),
    ("Country", "Country’s or territory short name"),
    ("Centroid", "Country’s centroid"),
    ("Lat", "Country’s Lat in decimal degrees"),
    ("Lon", "Country's Lon in decimal degrees"),
    ("Region", "IDMC regions"),
    ("Geographical region", "IDMC geographical regions"),
    ("Figure cause", "Cause or main driver of displacement:  Conflict: New displacements\
     due to conflict and other forms of violence. (colour code:  #EF7D04. Disasters:\
     New displacements due to natural hazards (colour code: #008ECA)"),
    ("Year", "Year of displacement"),
    ("Figure category", "Type of displacement metric"),
    ("Figure role", "Role of the figure. Recommended figures correspond to reporting\
     figures while triangulation figures correspond to figures used for triangulation."),
    ("Total figures", "Total figures in terms of people. Ex. If a figure is reported in\
     households we transform the figure into an estimated number of people by multipliying\
     the rerported figure with the AHHS"),
    ("Reported", "Reported figure. Figures can be reported in households of numbers of people"),
    ("Figure term", "Reported term used by the source of the figure"),
    ("Unit", "Unit of reporting. It can be households or people"),
    ("Quantifier", "Level of uncertainty or accuracy of the figure"),
    ("Household size", "Average household size. This values are comapiled by IDMC from UN and national sources."),
    ("Is housing destruction", "Housing destruction recommended figure (Yes/No)"),
    ("Displacement occurred", "Mark the time when displacement happened relative to the time of\
     the displacement driver. Displacement can ocurre as a prevention mechanism before shock that\
     drives displacement, during the shock or as a result of the shock."),
    ("Include in IDU", "Figure published as an Internal Displacement Update -I DU (Yes/No)"),
    ("Excerpt IDU", "IDU text"),
    ("Violence type", "Violence type as per IDMC methodology"),
    ("Violence sub type", "Violence sub type as per IDMC methodology"),
    ("OSV sub type", "OSV sub type as per IDMC methodology"),
    ("Context of violences", "Context of violences as per IDMC methodology"),
    ("Hazard category", "Hazard category as per EM-DAT definitions"),
    ("Hazard sub category", "Hazard sub category as per EM-DAT definitions"),
    ("Hazard type", "Hazard type as per EM-DAT definitions"),
    ("Hazard sub type", "Hazard sub type  as per EM-DAT definitions"),
    ("Other event sub type", "This category is selected when the driver of displacement \
     is not clear or when it  represents multiple driver types."),
    ("Start date", "start date of displacement flow"),
    ("Start date accuracy", "uncertanty or accuracy of start date"),
    ("End date", "end date of thedisplacement flow"),
    ("End date accuracy", "uncertanty or accuracy of end date"),
    ("Stock date", "Stock date"),
    ("Stock date accuracy", "uncertanty or accuracy of stock date"),
    ("Stock reporting date", "Stock reporting date. This date correspond to the IDMC reporting period."),
    ("Analysis and calculation logic", "Description of the calculation of the figures"),
    ("Link", "Link of the figure"),
    ("Publishers", "Publisher of the figure"),
    ("Sources", "Source of the figure"),
    ("Sources type", "Type of source"),
    ("Sources reliability", "Reliability of the source "),
    ("Sources methodology", "Methodology used by the source of the figure"),
    ("Source excerpt", "Source excerpt"),
    ("Source url", "Source url"),
    ("Source document", "Link to the document uploaded to Helix"),
    ("Locations name", "Name of locations were displacement was reported"),
    ("Locations", "Coordinates of the locations reported"),
    ("Type of point", "Accuracy of locations "),
    ("Entry ID", "Entry ID"),
    ("Entry old ID", "Legacy ID from Helix 1.0 "),
    ("Entry title", "Entry name"),
    ("Entry link", "Entry link"),
    ("Disability", "Has the dataset describes populations with disabilities (Yes/No)"),
    ("Indigenous people", "Has the dataset describes indigenous populations (Yes/No)"),
    ("Event ID", "Event ID"),
    ("Event old ID", "Legacy ID from Helix 1.0"),
    ("Event name", "Event name"),
    ("Event code", "Event or hazard unique identifiers. Ex. GLIDEnumber, FEMA ID, etc"),
    ("Event cause", "Cause or main driver of displacement event."),
    ("Event main trigger", "Event main hazard sub  type or conflict type"),
    ("Event start date", "Event or hazard start date"),
    ("Event end date", "Event or hazard end date date"),
    ("Event start date accuracy", "uncertanty or accuracy of event start date"),
    ("Event end date accuracy", "uncertanty or accuracy of event end date"),
    ("Event narrative", "Description of the event"),
    ("Crisis ID", "Crisis ID"),
    ("Crisis name", "Crisis name "),
    ("Tags", "Labels or tags that allow flagging different thematic areas."),
    ("Has age disaggregated data", "This toggle marks if the dataset has information\
     on age or or gender disaggregated data"),
    ("Revision progress", "Status of the revision progress"),
    ("Assignee", "Assignee responsible of the revision proce"),
    ("Created by", "Name of the expert that created the entry"),
    ("Updated by", "Name of the last persone modifiying the entry"),
]

READ_ME_DATA = [
    {
        'column_name': column_name,
        'description': description
    }
    for column_name, description in read_me_data_raw
]
