"""The areas the redlining story looks at closely, with the names the page gives them.

The 1937 forms for Richmond leave the area-name field blank, so these names are the story's:
each is placed from the streets, churches and parks inside the outline today (OpenStreetMap,
fetched November 16, 2026) and from the forms themselves (D4's form calls D3 "Oak Park").
"""
NAMES = {
    'A5': 'Windsor Farms',
    'D1': 'Jackson Ward, Apostle Town and Navy Hill',
    'D2': 'Washington Park, around Cheatwood Avenue',
    'D3': 'Oak Park, along Laburnum Avenue',
    'D4': 'Around Hunt and Hazelhurst Avenues',
    'D5': 'Fairmount and the blocks around Mosby Court',
    'D6': 'Union Hill and the slopes of Church Hill',
    'D7': 'Fulton',
    'D8': 'Randolph and Oregon Hill',
    'D9': 'Beside Maymont, then mostly vacant',
    'D10': 'South of the river, around Bainbridge and Perry Streets',
    'D11': 'Manchester, around Cowardin Avenue',
    'D11.5': 'Blackwell',
}
D_AREAS = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D11.5']


def slug(label):
    return label.lower().replace('.', '-')
