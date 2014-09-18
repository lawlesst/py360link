"""
Types to handle.

- articles
- books
- ebooks
- book chapters/parts
"""

from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ElementTree
import urllib
import urllib2

from sort_databases import do_sort

#Default timeout for calls to the API.
#Experience shows that requests with Pubmed IDs may take up to 10 seconds.
TIMEOUT = 10

#Namespaces for XML parsing.
ss = "{http://xml.serialssolutions.com/ns/openurl/v1.0}"
ssdiag = "{http://xml.serialssolutions.com/ns/diagnostics/v1.0}"
dc = "{http://purl.org/dc/elements/1.1/}"


def get(query, **params):
    """
    Method to query the API and return a response
    object.
    """
    api_key = params.get('key')
    api_timeout = params.get('timeout', TIMEOUT)
    response_url, api_response = get_api_response(query, api_key, api_timeout)
    resp = Response(api_response,
                    api_url=response_url)
    return resp


def get_api_response(query, key, timeout):
    """
    Get the SerSol API response and parse it into an etree.
    """
    if key is None:
        raise Link360Exception('Serial Solutions 360Link XML API key is required.')
    required_url_elements = {}
    required_url_elements['version'] = '1.0'
    required_url_elements['url_ver'] = 'Z39.88-2004'
    #Go get the 360link response
    #Base 360Link url
    base_url = "http://%s.openurl.xml.serialssolutions.com/openurlxml?" % key
    base_url += urllib.urlencode(required_url_elements)
    url = base_url + '&%s' % query.lstrip('?')
    resp = urllib2.urlopen(url, timeout=timeout)
    return (resp.geturl(), resp)


class Item(object):

    def __init__(self, item):
        """
        Parse an individual result from the 360Link API.
        """
        self.item = item
        self.citation = self.get_citation()
        self.format = self.get_format()
        self.title = self.get_title()
        self.source = self.get_source()
        self.btype = self.get_btype()

    def get_format(self):
        """
        Format as returned by 360Link.
        """
        format = self.item.attrib.get('format')
        return format

    def get_citation(self):
        citation = pull(self.item, '{0}citation')
        return citation

    def get_source(self):
        source = pull(self.citation, '{1}source', text=True)
        return source

    def get_title(self):
        title = pull(self.citation, '{1}title', text=True)
        #Check source if title is blank
        if title is None:
            return pull(self.citation, '{1}source', text=True)
        return title

    def get_btype(self):
        format = self.format
        source = self.source
        title = self.title
        btype = 'Unknown'
        if format == 'journal':
            if (source is not None) and (title is None):
                btype = 'journal'
            else:
                btype = 'article'
        elif format == 'book':
            #Test for chapter - seems like the best we can do is look for a start page in the response.
            if (source is not None) and (self.meta().get('spage') is not None):
                btype = 'inbook'
            else:
                btype = 'book'
        return btype

    def meta(self):
        m = {}
        isns = []
        for child in self.citation.getchildren():
            #Remove namespaces
            tag = child.tag.replace(ss, '').replace(dc, '')
            #Handle print or electronic isbns.
            #These two tags are repeating.
            if (tag == 'isbn') or (tag == 'issn'):
                if child.attrib.get('type') == 'electronic':
                    if tag == 'isbn':
                        isns.append(('eisbn', child.text))
                    elif tag == 'issn':
                        isns.append(('eissn', child.text))
                else:
                    isns.append((tag, child.text))
            else:
                m[tag] = child.text
        m['isn'] = isns
        return m

    def get_links(self, sort=False, remove_duplicates=True, article_only=True):
        #One linkGroup with many linkGroups.
        link_groups = pull(self.item, '{0}linkGroups')
        if link_groups is None:
            return
        links = []
        #Holder so we don't add duplicates.
        seen_links = []
        seen_providers = []
        for group in link_groups:
            provider = pull(group, '{0}holdingData/{0}providerName', text=True)
            #Don't offer multiple links from the same provider.
            if provider in seen_providers:
                continue
            else:
                seen_providers.append(provider)
            database = pull(group, '{0}holdingData/{0}databaseName', text=True)
            #Coverage start and end.
            #<ssopenurl:normalizedData>
            #<ssopenurl:startDate>2000-01-01</ssopenurl:startDate>
            #<ssopenurl:endDate>2004-12-31</ssopenurl:endDate>
            cstart = pull(group, '{0}holdingData/{0}normalizedData/{0}startDate', text=True)
            cend = pull(group, '{0}normalizedData/{0}endDate', text=True)

            #links
            urls = pull(group, '{0}url', findall=True)
            for url in urls:
                #Don't offer the same url twice.
                if (remove_duplicates is True) and (url in seen_links):
                    continue
                l = {}
                l['provider'] = provider
                l['url'] = url.text
                link_type = url.attrib.get('type')
                l['type'] = link_type
                #Make sense out of the various links returned from SerSol.
                if link_type == 'article':
                    l['anchor'] = 'Full text available from %s.' % database
                elif link_type == 'source':
                   l['anchor'] = provider
                elif link_type == 'journal':
                    l['anchor'] = 'Journal website'
                elif link_type == 'issue':
                    l['anchor'] = 'Browse this issue'
                else:
                    l['anchor'] = provider
                #coverage
                if cstart is not None:
                    l['coverage_start'] = cstart
                if cend is not None:
                    l['coverage_end'] = cend

                links.append(l)
                seen_links.append(url)

        if sort is True:
            return do_sort(links)
        return links

    def bibjson(self):
        """
        Convert an Item to bibjson.
        """
        citation = self.meta()
        bib = {}
        bib['type'] = self.get_btype()
        bib['links'] = self.get_links()
        #TODO: Handle book chapter/inbook source titles.  Now handled like journals.
        #journal names
        if bib['type'] != 'book':
            bib['journal'] = {'name': citation.get('source')}
        #pages
        bib['start_page'] = citation.get('spage')
        #title and author are the same for all fromats in bibjson
        bib['title'] = citation.get('title')
        author = [
            {
                'name': citation.get('creator'),
                'firstname': citation.get('creatorFirst'),
                'lastname': citation.get('creatorLast')
            }
        ]
        #ToDo: Pull out empty keys for authors
        bib['author'] = author
        bib['year'] = citation.get('date', '-').split('-')[0]
        bib['issue'] = citation.get('issue')
        bib['volume'] = citation.get('volume')
        bib['publisher'] = citation.get('publisher')
        bib['address'] = citation.get('publicationPlace')

        #Get potential identifiers
        ids = [
            {
                'type': 'doi',
                'id': citation.get('doi')
            },
            {
                'type': 'issn',
                'id': citation.get('issn', {}).get('print')
            },
            {
                'type': 'eissn',
                'id': citation.get('eissn')
            },
            {
                'type': 'pmid',
                'id': citation.get('pmid')
            }
        ]
        ids = filter(lambda id: id['id'] is not None, ids)
        #add isbns to identifiers
        isbns = citation.get('isbn', [])
        for isbn in isbns:
            ids.append({'type': 'isbn',
                        'id': isbn})
        bib['identifier'] = ids
        return bib


class Response(object):

    def __init__(self, api_response, **kwargs):
        tree = ElementTree()
        self.tree = tree.parse(api_response)
        self.url = kwargs.get('api_url', None)
        self.records = self.results()
        self.total = len(self.records)

    def results(self):
        results = self.tree.findall('*/{0}result'.format(ss))
        out = []
        for result in results:
            out.append(Item(result))
        return out

    def raw(self):
        #import ipdb; ipdb.set_trace()
        xml = ET.tostring(self.tree, 'utf-8')
        return xml

    @property
    def query(self):
        """
        Get the raw query from the SerSol response.
        """
        query = self.tree.find('*/{0}queryString'.format(ss,)).text
        return query

    @property
    def library(self):
        """
        Get the library name from the response.
        """
        lib = self.tree.find('*/{0}library/{0}name'.format(ss,)).text
        return lib

    @property
    def library_id(self):
        """
        Get the code associated with the library.
        """
        lib = self.tree.find('*/{0}library'.format(ss,))
        code = lib.attrib.get('id')
        return code

    def json(self):
        out = {}
        meta = {}
        meta['size'] = self.total
        try:
            meta['library'] = self.library
        except AttributeError:
            raise Link360Exception("Error communicating with 360 link.  Verify url %s." % self.url)
        meta['url'] = self.url
        out['metadata'] = meta
        out['records'] = [
            item.bibjson()
            for item in self.results()
        ]
        return out


def pull(elem, path, findall=False, text=False):
    """
    XML parsing helper.
    """
    if findall is True:
        if elem is not None:
            return elem.findall(path.format(ss, dc))
        else:
            return []
    else:
        _this = elem.find(path.format(ss, dc))
        if text is True:
            try:
                return _this.text
            except AttributeError:
                return
        else:
            return _this


class Link360Exception(Exception):
    pass
