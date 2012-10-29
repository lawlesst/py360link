"""
Sort a list of links to databases.

It's expecting to sort on a key of 'provider'
"""


#For sorting databases returned by provider.
SORT_BY = ['JSTOR']
#Providers in this list will be forced to the top.
PUSH_TOP = ['Elsevier']
#Providers in this list will be forced to the bottom.
PUSH_BOTTOM = ['LexisNexis']

def do_sort(links):
    """
    Sort the links returned by library defined criteria.
    http://stackoverflow.com/questions/10274868/sort-a-list-of-python-dictionaries-depending-on-a-ordered-criteria

    A high value will push the link to the bottom of the list.
    A low or negative value will bring it to the front.
    """
    criteria = SORT_BY
    def _mapped(provider):
        if provider in PUSH_TOP:
            return -10
        elif provider in PUSH_BOTTOM:
            return 10
        else:
            return 1
    links.sort(key=lambda x: criteria.index(x['provider'])\
             if x['provider'] in criteria\
             else _mapped(x['provider']))
    return links
