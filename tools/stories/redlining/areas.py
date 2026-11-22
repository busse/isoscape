"""The areas the redlining story looks at closely, with the names the page gives them.

The 1937 form has no name field. Some of Richmond's forms carry a typed heading with a place
name (among the D areas: D6 Church Hill, D7 Fulton, D9 Riverview, D11 South Richmond; and A5
Windsor Farms), and D4's form calls D3 Oak Park. The names here are the story's, chosen to orient
a reader today (the owner's decision, November 22, 2026): from those headings where they still
serve, otherwise from the streets, churches and parks inside the outline today (OpenStreetMap,
fetched November 16, 2026).
"""
NAMES = {
    'A5': 'Windsor Farms',
    'D1': 'Jackson Ward, Apostle Town and Navy Hill',
    'D2': 'Washington Park, around Cheatwood Avenue',
    'D3': 'Oak Park, along Laburnum Avenue',
    'D4': 'Around Hunt and Hazelhurst Avenues',
    'D5': 'Fairmount and the blocks around Mosby Court',
    'D6': 'Church Hill and Union Hill',
    'D7': 'Fulton',
    'D8': 'Randolph and Oregon Hill',
    'D9': 'Riverview, beside Maymont',
    'D10': 'South of the river, around Bainbridge and Perry Streets',
    'D11': 'Manchester, around Cowardin Avenue',
    'D11.5': 'Blackwell',
}
D_AREAS = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D11.5']


def slug(label):
    return label.lower().replace('.', '-')
