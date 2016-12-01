#!/usr/bin/env python

import urlparse as up
from pprint import pprint
from os.path import abspath, dirname, join
from urllib import urlencode
from urllib2 import urlopen
import requests as rq
from bs4 import BeautifulSoup
import json

pwd = abspath(dirname(__file__))

DEBUG = False

default_parser = 'html5lib'

def main():
    from sys import argv
    url = argv[1]
    show_url_specs(url)

    print('Program Complete.')

## GENERAL UTILS ##
def got_string(string):
    def got_string_func(item):
        if item is not None:
            return string in item
        else:
            return False
    return got_string_func

## URL UTILS ##

def show_url_specs(url):

    u = up.urlparse(url)
    q = up.parse_qs(u.query)

    print('\n------------\n')
    print('Host Address: {}'.format(u.hostname))
    print('Path: {}'.format(u.path))
    if len(q) > 0:
        print('Query components:')
        pprint(q)

def bs_from_url(url, *args, **kwargs):
    resp = rq.get(url, *args, **kwargs)
    return BeautifulSoup(resp.text, default_parser)

## LINKEDIN UTILS ##

def lnkdn_location_ids():
    from csv import reader
    filepath = join(pwd, 'linkedin_locationids.csv')
    place_id_list = []
    for id, place in reader(open(filepath, 'r')):
        place_id_list.append((place, id))

    place_id_dict = dict(place_id_list)
    return place_id_dict

def lnkdn_jobs_search_soup(keywords, page=1, bs_parser='html5lib', location='San Francisco Bay Area', locationId='us:84', searchOrigin='JSERP',
                           trk='jobs_jserp_search_button_execute'):
    uscheme = 'https'
    unetloc = 'www.linkedin.com'
    upath = 'jobs/search'
    # uparams = ''
    qd = {'keywords': keywords,
          'location': location,
          'locationId': locationId,
          'searchOrigin': searchOrigin,
          'trk': trk,
          }

    # TODO: Test out this 'page' => start query functionality.  Cursory browser testing seems to
    # [TODO] indicate 'start' is the key page alterer
    if page > 1:
        qd['start'] = str((page-1)*25)

    base_path = 'https://www.linkedin.com/jobs/search'
    lrq = rq.get(base_path, params=qd)
    bs = BeautifulSoup(lrq.text, bs_parser)

    if DEBUG:
        print(base_path)
        pprint(qd)
    return bs

def lnkdn_job_postings(job_search_soup):
    from json import loads
    jbs = job_search_soup.findAll('code', attrs={'id': 'decoratedJobPostingsModule'})
    jbc = jbs[0].contents[0]
    js = loads(jbc)
    # more filters
    urls = []
    for element in js['elements']:
        urls.append(element.get('viewJobTextUrl'))

    # TODO: Look at js['pagination'] data to see if more fine-tuned page control can be achieved.
    return js, urls


# TODO: Get Other Job Postings Scrape Items:
# TODO:     jobDescriptionModule, seoModule
# TODO: These vary from posting to posting, will have to work logic around this.
def lnkdn_job_posting_dicts(url):
    lrq = rq.get(url)
    soup = BeautifulSoup(lrq.text, 'html5lib')

    # og_string - how we tell if it has a useful property field
    og_string = 'og:'
    got_og_string = got_string(og_string)
    og_items = soup.findAll('meta', attrs={'property':got_og_string})

    # OG dict
    og_dict = {}
    for item in og_items:
        #print('Property: {}'.format(item['property']))
        #print('Content:\n{}'.format(item['content']))
        #print('------------------')

        property = item['property'].encode('utf-8')
        #property = item['property']
        property = property.replace(og_string, '')
        content = item['content'].encode('utf-8')
        #content = item['content']
        og_dict[property] = content

    # seoModule
    seo_dict = json.loads(soup.find('code', attrs={'id':'seoModule'}).contents[0].encode('utf-8'), encoding='utf-8')

    #jobDescriptionModule
    job_description_dict = json.loads(soup.find('code', attrs={'id': 'jobDescriptionModule'}).contents[0].encode('utf-8'), encoding='utf-8')

    return og_dict, seo_dict, job_description_dict

    return job_description_dict

    return seo_dict

    return og_dict

    #''' <meta property="og:description" content=" '''
    #descrip = soup.find('meta', attrs={'property': "og:description"})
    #return descrip



if __name__ == "__main__":
    main()