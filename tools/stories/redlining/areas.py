"""The areas the redlining story looks at closely: their 1937 headings and the page's names.

The 1937 form has no name field. Some of Richmond's forms carry a typed heading with a place
name (among the D areas: D6 Church Hill, D7 Fulton, D9 Riverview, D11 South Richmond; and A5
Windsor Farms). Titles follow the owner's format (November 22, 2026, `title`): the number, the
heading where there is one, and in parentheses the page's modern name where it differs. The
modern names are the story's, placed from the streets, churches and parks inside each outline
today (OpenStreetMap, fetched November 16, 2026). D4's form reads "Same as Oak Park, D2." (scan
p. 40, field 14; the Lab's transcription has "D3"), so Oak Park is what another area's form calls
D2: it is not D2's own heading, and D2's title keeps the number and modern name only.
"""
D_AREAS = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D11.5']


def slug(label):
    return label.lower().replace('.', '-')

# The 1937 form's typed heading, exactly as the scan gives it (FRASER ad_RichmondVA.pdf; page in
# HEADING_PAGE), for the areas that have one. Areas without a heading have no historic name.
HISTORIC = {'A5': 'Windsor Farms', 'D6': 'Church Hill', 'D7': 'Fulton', 'D9': 'Riverview', 'D11': 'South Richmond'}
HEADING_PAGE = {'A5': 5, 'D6': 42, 'D7': 43, 'D9': 45, 'D11': 48}
# The page's modern names, chosen to orient a reader today; None where the historic name serves.
MODERN = {
    'A5': None,
    'D1': 'Jackson Ward, Apostle Town and Navy Hill',
    'D2': 'Washington Park, around Cheatwood Avenue',
    'D3': 'along Laburnum Avenue',
    'D4': 'around Hunt and Hazelhurst Avenues',
    'D5': 'Fairmount and the blocks around Mosby Court',
    'D6': 'Union Hill and the slopes of Church Hill',
    'D7': None,
    'D8': 'Randolph and Oregon Hill',
    'D9': 'between Maymont and the river',
    'D10': 'south of the river, around Bainbridge and Perry Streets',
    'D11': 'Manchester, around Cowardin Avenue',
    'D11.5': 'Blackwell',
}


def title(label):
    """The owner's format (November 22, 2026): "{number}, {historic name} ({modern name})", the
    parentheses only when the modern name differs; with no historic name, "{number} ({modern})",
    so parentheses always mean the page's modern name."""
    h, m = HISTORIC.get(label), MODERN.get(label)
    if h and m:
        return f'{label}, {h} ({m})'
    if h:
        return f'{label}, {h}'
    return f'{label} ({m})'


# The grades as the Richmond map's legend prints them, and the HOLC's names for them as handwritten
# on the legend of its map of Atlanta (both National Archives, RG 195, via FRASER).
GRADE_LEGEND = {'A': 'First Grade', 'B': 'Second Grade', 'C': 'Third Grade', 'D': 'Fourth Grade'}
GRADE_NAME = {'A': 'Best', 'B': 'Still Desirable', 'C': 'Definitely Declining', 'D': 'Hazardous'}
KEY_LABELS = [f'{g} {GRADE_LEGEND[g]}, "{GRADE_NAME[g]}"' for g in 'ABCD']
KEY_TITLE = "Grades on the Home Owners' Loan Corporation's (HOLC's) 1937 map"
KEY_SOURCE = ("Grade names: the Richmond map's legend (First to Fourth Grade); the names in quotation marks "
              "as handwritten on the legend of the HOLC's map of Atlanta (National Archives, RG 195, via FRASER)")
