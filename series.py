
import wbgapi as w
from . import series_metadata as metadata

def list(id='all'):
    '''Iterate over the list of indicators/series in the current database

    Returns:
        a generator object

    Example:
        for elem in wbgapi.series.list():
            print(elem['id'], elem['value'])

    '''
    return w.source.features('series', w.queryParam(id))

def get(id):
    '''Get a single indicator object

    Parameters:
        id:     The object ID

    Returns:
        A database object

    Example:
        print(wbgapi.series.get('SP.POP.TOTL')['value'])
    '''

    return w.source.feature('series', id)


def metadata_fetch(id,countries=[],time=[]):
    '''Return metadata for specified series

    Arguments:
        id:         The series ID or an array of series ID's to return metadata for

        countries:  Optional list of countries for which to include series-country metadata

    Returns:
        A generator object
    '''

    pg_size = 50    # large 2-dimensional metadata requests must be paged or the API will barf
                    # this sets the page size. Seems to work well even for very log CETS identifiers

    if type(countries) is str:
        countries = [countries]

    if type(time) is str:
        time = [time]

    url = '{}/{}/sources/{}/series/{}/metadata'.format(w.endpoint, w.lang, w.db, w.queryParam(id))
    for row in w.metadata(url):
        if countries:
            row.countries = {}
            n = 0
            while n < len(countries):
                cs = ';'.join(['{}~{}'.format(elem,row.id) for elem in countries[n:n+pg_size]])
                n += pg_size
                url2 = '{}/{}/sources/{}/Country-Series/{}/metadata'.format(w.endpoint, w.lang, w.db, cs)

                try:
                    for row2 in w.metadata(url2):
                        # w.metadata should be returning single entry dictionaries here since it pages for each new identifier
                        row.countries[row2.id.split('~')[0]] = row2.metadata['Country-Series']
                except:
                    raise

        if time:
            row.time = {}
            n = 0
            while n < len(time):
                st = ';'.join(['{}~{}'.format(row.id,elem) for elem in time[n:n+pg_size]])
                n += pg_size
                url2 = '{}/{}/sources/{}/Series-Time/{}/metadata'.format(w.endpoint, w.lang, w.db, st)

                try:
                    for row2 in w.metadata(url2):
                        row.time[row2.id.split('~')[1]] = row2.metadata['Series-Time']
                except:
                    pass

        yield row


def metadata_get(id,countries=[],time=[]):
    
    for row in metadata_fetch(id, countries, time):
        return row