
# Indeed API
from argparse import ArgumentParser
import urllib, json
import requests as rq
from bs4 import BeautifulSoup

def get_pub_ip():
    data = json.loads(urllib.urlopen("http://ip.jsontest.com/").read())
    return data["ip"]

## Defaults
LIMIT_DEFAULT = 100
RADIUS_DEFAULT = 15

## Countries and Cities
US = 'us'

SAN_FRAN = "San Francisco, CA"
SAN_DIEGO = 'San Diego, CA'
AUSTIN = 'Austin, TX'
SEATTLE = 'Seattle, WA'
PITTSBURGH = 'Pittsburgh, PA'
WASHINGTON_DC = 'Washington, DC'
CAMBRIDGE_US = 'Cambridge, MA'
US_CITIES = (SAN_DIEGO, SAN_FRAN, SEATTLE, AUSTIN, PITTSBURGH, WASHINGTON_DC, CAMBRIDGE_US)

UK = 'uk'

LONDON = 'London'
CAMBRIDGE_UK = 'Cambridge'
UK_CITIES = (LONDON, CAMBRIDGE_UK)

ALL_COUNTRIES = (US, UK)
ALL_CITIES = US_CITIES + UK_CITIES

def main():
    args = get_args()
    query = args.query
    location = args.location
    country = args.country
    limit = args.limit
    
    resp = indeed_request_raw(query, location, limit=limit)
    print(resp)

def get_args():
    ''' Argument parsing for CLI main() method. '''
    def low(s):
        ''' Returns s.lower for case insensitivity. '''
        return s.lower()
    
    ap = ArgumentParser(description="Use Indeed API.")
    
    ap.add_argument('query', default='developer', help='Search string.')
    
    ap.add_argument('location', default='San Francisco, CA', 
                    help='Location of job.', choices=ALL_CITIES)
                    
    ap.add_argument('-country', type=low, choices=ALL_COUNTRIES, help='Country (optional).')
    
    ap.add_argument('-limit', metavar='NUMBER', dest='limit', 
                    default=LIMIT_DEFAULT, type=int, 
                    help='Number of entries returned.')
                    
    args = ap.parse_args()
    return args


def indeed_request_raw(query, location, radius=None, country=None, limit=None):
    ''' Returns the plain JSON string. '''
    base_url = 'http://api.indeed.com/ads/apisearch'
    user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"
    my_ip = get_pub_ip()
    my_pub_id = get_pub_id()
    
    if radius is None:
        radius = RADIUS_DEFAULT
    
    if limit is None:
        limit = LIMIT_DEFAULT
    
    if country is None:
        country = get_country(location)
    
    indeed_params = {
        'userip': my_ip,
        'useragent': user_agent,
        'publisher' : str(my_pub_id),
        'v' : str(2),
        'format' : "json",
        #callback : None,
        'q' : query,
        'l' : location,
        'sort' : "relevance",
        'radius' : str(radius),
        'st' : '',
        'jt' : 'fulltime',
        'start' : '',
        'limit' : str(limit),
        'fromage' : '',
        #'highlight' : '',
        'latlong' : '1',
        'co': country } 
        
    return rq.get(base_url, params=indeed_params).text.encode('utf-8')
    
    
def indeed_request(query, location, **kw):
    ''' Returns the Python JSON object of the json string. '''
    raw_json = indeed_request_raw(query, location, **kw)
    return json.loads(raw_json)
    
def get_country(city):
    if city in US_CITIES:
        return US
    elif city in UK_CITIES:
        return UK
    
def get_pub_id():
    pub_id = None
    try:
        with open('publisher_id.txt', 'r') as id_file:
            pub_id = int(id_file.read().strip())
    except:
        raise
    return pub_id
    
	
if __name__ == "__main__":
	main()