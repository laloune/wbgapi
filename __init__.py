
'''This module provides a very rudimentary interface to the World Bank's data API.

Currently only low-level functionality is defined, but the aspiration is this
will improve over time to take advantage of the latest API functionality, as
well as perhaps compensate for some of its flaws.
'''

import urllib
import requests
import series

# defaults
endpoint = 'https://api.worldbank.org/v2'
lang = 'en'
db = 2

_aggs = None

class APIError(Exception):
  def __init__(self,url,msg,code=None):
    self.msg  = msg
    self.url  = url
    self.code = code

  def __str__(self):
    if self.code:
        return 'APIError: [{}] {} ({})'.format(self.code, self.msg, self.url)

    return 'APIError: {} ({})'.format(self.msg, self.url)


def fetch(url,params={}):
    '''Iterate over an API response with automatic paging

    Parameters:
        url: full URL for the API query, minus the query string

        params: optional query string parameters (required defaults are supplied by the function)

    Returns:
        a generator object

    Example:
        for row in wbgapi.fetch('https://api.worldbank.org/countries'):
          print row['name']
    '''

    params_ = {'per_page': 100}
    params_.update(params)
    params_['page'] = 1
    params_['format'] = 'json'

    totalRecords = None

    recordsRead = 0
    while totalRecords is None or recordsRead < totalRecords:

        url_ = '{}?{}'.format(url, urllib.urlencode(params_))
        (hdr,result) = _queryAPI(url_)

        if totalRecords is None:
            totalRecords = int(hdr['total'])

        data = _responseObjects(url_, result)
        for elem in data:
            yield elem

        recordsRead += int(hdr['per_page'])
        params_['page'] += 1

def get(url,params={}):
    '''Return a single response from the API

    Parameters:
        url: full URL for the API query, minus the query string

        params: optional query string parameters (required defaults are supplied by the function)

    Returns:
        First row from the response

    Example:
        print wbgapi.get('https://api.worldbank.org/countries/BRA')['name']
    '''

    params_ = params.copy()
    params_['page'] = 1
    params_['format'] = 'json'
    params_['per_page'] = 1

    url_ = url + '?' + urllib.urlencode(params_)
    (hdr,result) = _queryAPI(url_)
    data = _responseObjects(url_, result)
    return data[0] if len(data) > 0 else None


def agg_list():

    global _aggs, endpoint

    if type(_aggs) is set:
        return _aggs

    url = '{}/country/all'.format(endpoint)
    _aggs = set()
    for row in fetch(url):
        if row['region']['id'] == 'NA':
            _aggs.add(row['id'])
            _aggs.add(row['iso2Code'])

    return _aggs
        

def _responseHeader(url, result):
    '''Internal function to return the response header, which contains page information
    '''

    if type(result) is list and len(result) > 0 and type(result[0]) is dict:
        # looks like the v2 data API
        return result[0]

    if type(result) is dict:
        # looks like the new beta advanced API
        return result

    raise APIError(url, 'Unrecognized response object format')

def _responseObjects(url, result):
    '''Internal function that returns an array of objects
    '''

    if type(result) is list and len(result) > 1:
        # looks like the v2 data API
        return result[1]

    if type(result) is dict and result.get('source'):
        if type(result['source']) is list:
            return result['source'][0]['concept'][0]['variable']

        if type(result['source']) is dict:
            return result['source']['data']

    raise APIError(url, 'Unrecognized response object format')

def _queryAPI(url):
    '''Internal function for calling the API with sanity checks
    '''
    response = requests.get(url)
    if response.status_code != 200:
        raise APIError(url, response.reason, response.status_code)

    try:
        result = response.json()
    except:
        raise APIError(url, 'JSON decoding error')

    hdr = _responseHeader(url, result)
    if hdr.get('message'):
        msg = hdr['message'][0]
        raise APIError(url, '{}: {}'.format(msg['key'], msg['value']))

    return (hdr, result)

def _apiParam(arg):
    ''' convert an API parameter to a semicolon-delimited string
    '''

    if type(arg) is str and len(arg) > 0:
        return arg

    if type(arg) is list:
        return ';'.join(arg)

    return None

