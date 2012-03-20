import urllib
from lxml import etree
import urlparse

SERSOL_KEY = None

#Make the OpenURL for passing on.
SERSOL_MAP = {
    'journal': {
        'title': 'atitle',
        'creatorLast': 'aulast',
        'creator': 'au',
        'creatorFirst': 'aufirst',
        'creatorMiddle': 'auinitm',
        'source': 'jtitle',
        'date': 'date',
        #issns are tricky - handle in application logic
        'issn': 'issn',
        'eissn': 'eissn',
        'isbn': 'isbn',
        'volume': 'volume',
        'issue': 'issue',
        'spage': 'spage',
        #dois and pmids need to be handled differently too.
        #This mapping is here just to retain their original keys.
        'doi': 'doi',
        'pmid': 'pmid',
        #'publisher': 'publisher'
        #publicationPlace
        },
    'book': {
        'publisher': 'pub',
        'isbn': 'isbn',
        'title': 'btitle',
        'date': 'date',
        'creator': 'author',
        'creatorLast': 'aulast',
        'creatorLast': 'aulast',
        'creatorFirst': 'aufirst',
        'creatorMiddle': 'auinitm',
        'isbn': 'isbn',
        'title': 'btitle',
        'date': 'date',
        'publicationPlace': 'place',
        'format': 'genre',
        'source': 'btitle',
    }
}

class Link360Exception(Exception):
    def __init__self(self, message, Errors):
        #http://stackoverflow.com/questions/1319615/proper-way-to-declare-custom-exceptions-in-modern-python
        Exception.__init__(self, message)
        self.Errors = Errors

def get_sersol_response(query, key, timeout):
    """
    Get the SerSol API response and parse it into an etree.
    """
    import urllib2
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
    f = urllib2.urlopen(url, timeout=timeout)
    doc = etree.parse(f)
    return doc

def get_sersol_data(query, key=None, timeout=5):
    """
    Get and process the data from the API and store in Python dictionary.
    If you would like to cache the 360Link responses, this is data structure
    that you would like to cache.  
    
    Specify a timeout for the http request to 360Link.
    
    """
    if query is None:
        raise Link360Exception('OpenURL query required.')
    doc = get_sersol_response(query, key, timeout)
    data = Link360JSON(doc).convert()
    return data

class Link360JSON(object):
    """
    Convert Link360 XML To JSON
    follows http://xml.serialssolutions.com/ns/openurl/v1.0/ssopenurl.xsd
    Godmar Back <godmar@gmail.com>, May 2009
    """
    def __init__(self, doc):
        self.doc = doc

    def convert(self):

        ns = {
            "ss" : "http://xml.serialssolutions.com/ns/openurl/v1.0",
            "sd" : "http://xml.serialssolutions.com/ns/diagnostics/v1.0",
            "dc" : "http://purl.org/dc/elements/1.1/"
        }

        def x(xpathexpr, root = self.doc):
            return root.xpath(xpathexpr, namespaces=ns)

        def t(xpathexpr, root = self.doc):
            r = x(xpathexpr, root)
            if len(r) > 0:
                return r[0]
            return None

        def m(dict, *kv):
            """merge (k, v) pairs into dict if v is not None"""
            for (k, v) in kv:
                if v:
                    dict[k] = v
            return dict

        return m({ 
            'version' : t("//ss:version/text()"),
            'echoedQuery' : {
                'queryString' : t("//ss:echoedQuery/ss:queryString/text()"),
                'timeStamp' : t("//ss:echoedQuery/@timeStamp"),
                'library' : {
                    'name' : t("//ss:echoedQuery/ss:library/ss:name/text()"),
                    'id' : t("//ss:echoedQuery/ss:library/@id")
                }
            },
            'dbDate' : t("//ss:results/@dbDate"),
            'results' : [ {
                'format' : t("./@format", result),
                'citation' : m({ },
                    ('title', t(".//dc:title/text()")),
                    ('creator', t(".//dc:creator/text()")),
                    ('source', t(".//dc:source/text()")),
                    ('date', t(".//dc:date/text()")),
                    ('publisher', t(".//dc:publisher/text()")),
                    ('creatorFirst', t(".//ss:creatorFirst/text()")),
                    ('creatorMiddle', t(".//ss:creatorMiddle/text()")),
                    ('creatorLast', t(".//ss:creatorLast/text()")),
                    ('volume', t(".//ss:volume/text()")),
                    ('issue', t(".//ss:issue/text()")),
                    ('spage', t(".//ss:spage/text()")),
                    ('doi', t(".//ss:doi/text()")),
                    ('pmid', t(".//ss:pmid/text()")),
                    ('publicationPlace', t(".//ss:publicationPlace/text()")),
                    ('institution', t(".//ss:institution/text()")),
                    ('advisor', t(".//ss:advisor/text()")),
                    ('patentNumber', t(".//ss:patentNumber/text()")),
                    # assumes at most one ISSN per type
                    ('issn', dict([ (t("./@type", issn), t("./text()", issn))
                                   for issn in x("//ss:issn") ])),
                    ('eissn', t(".//ss:eissn/text()")),
                    ('isbn', [ t("./text()", isbn) for isbn in x("//ss:isbn") ])
                ),
                'linkGroups' : [ {
                    'type' : t("./@type", group),
                    'holdingData' : m({ 
                            'providerId' : t(".//ss:providerId/text()", group),
                            'providerName' : t(".//ss:providerName/text()", group),
                            'databaseId' : t(".//ss:databaseId/text()", group),
                            'databaseName' : t(".//ss:databaseName/text()", group),
                        },
                        # output normalizedData/startDate instead of startDate, 
                        # assuming that 'startDate' is redundant
                        ('startDate' , t(".//ss:normalizedData/ss:startDate/text()", group)),
                        ('endDate' , t(".//ss:normalizedData/ss:endDate/text()", group))),
                    # assumes at most one URL per type
                    'url' : dict([ (t("./@type", url), t("./text()", url)) 
                                   for url in x("./ss:url", group) ])
                } for group in x("//ss:linkGroups/ss:linkGroup")]
            } for result in x("//ss:result") ] }, 
            # optional
            ('diagnostics', 
                [ m({ 'uri' : t("./sd:uri/text()", diag) },
                    ('details', t("./sd:details/text()", diag)), 
                    ('message', t("./sd:message/text()", diag))
                ) for diag in x("//sd:diagnostic")]
            )
            # TBD derivedQueryData
        )
        

class Resolved(object):
    """
    Object for handling resolved Sersol queries.
    """
    def __init__(self, data):
        self.data = data
        self.query = data['echoedQuery']['queryString']
        self.query_dict = urlparse.parse_qs(self.query)
        error = self.data.get('diagnostics', None)
        if error:
            msg = ' '.join([e.get('message') for e in error if e])
            raise Link360Exception(msg)
        
        #Shortcut to first returned citation and link group
        self.citation = data['results'][0]['citation']
        self.link_groups = data['results'][0]['linkGroups']
        self.format = data['results'][0]['format']
    
        
    @property
    def openurl(self):
        return urllib.urlencode(self.openurl_pairs(), doseq=True)
    
    @property
    def oclc_number(self):
        """
        Parse the original query string and retain certain key, values.
        Primarily meant for storing the worldcat accession number passed on
        by Worldcat.org/FirstSearch
        """
        import re
        reg = re.compile('\d+')
        dat = self.query_dict.get('rfe_dat', None)
        if dat:
            #get the first one because dat is a list
            match = reg.search(dat[0])
            if match:
                return match.group()
        return
    
    def _retain_ourl_params(self):
        """
        Parse the original query string and retain certain key, values.
        Primarily meant for storing the worldcat accession number passed on
        by http://worldcat.org or FirstSearch.
        
        This could be also helpful for retaining any other metadata that won't
        be returned from the 360Link API.
        """
        retain = ['rfe_dat', 'rfr_id', 'sid']
        parsed = urlparse.parse_qs(self.query)
        out = []
        for key in retain:
            val = parsed.get(key, None)
            if val:
                out.append((key, val))
        return out
    
    def openurl_pairs(self):
        """
        Create a default OpenURL from the given citation that can be passed
        on to other systems for querying.
          
        Subclass this to handle needs for specific system.
        
        See http://ocoins.info/cobg.html for implementation guidelines.
        """
        query = urlparse.parse_qs(self.query)
        format = self.format
        #Pop invalid rft_id from OCLC
        try:
            
            if query['rft_id'][0].startswith('info:oclcnum'):
                del query['rft_id']
        except KeyError:
            pass
        #Massage the citation into an OpenURL
        #Using a list of tuples here to account for the possiblity of repeating values.
        out = []
        for k, v in self.citation.items():
            #Handle issns differently.  They are a dict in the 360LinkJSON response.
            if k == 'issn':
                issn_dict = self.citation[k]
                if isinstance(issn_dict, dict):
                    issn = issn_dict.get('print', None)
                else:
                    issn = issn_dict
                if issn:
                    out.append(('rft.issn', issn))
                continue
            #Handle remaining keys. 
            try:
                k = SERSOL_MAP[format][k]
            except KeyError:
                pass
            #handle ids separately 
            if (k == 'doi'):
                out.append(('rft_id', 'info:doi/%s' % v))
            elif (k == 'pmid'):
                #We will append a plain pmid for systems that will resolve that.
                out.append(('pmid', v))
                out.append(('rft_id', 'info:pmid/%s' % v))
            else:
                out.append(('rft.%s' % k, v))
        #versioning
        out.append(('url_ver', 'Z39.88-2004'))
        out.append(('version', '1.0'))
        #handle formats
        if format == 'book':
            out.append(('rft_val_fmt', 'info:ofi/fmt:kev:mtx:book'))  
            out.append(('rft.genre', 'book'))
        #for now will treat all non-books as journals
        else:
            out.append(('rft_val_fmt', 'info:ofi/fmt:kev:mtx:journal')) 
            out.append(('rft.genre', 'article'))
        #Get the special keys.   
        retained_values = self._retain_ourl_params()
        out += retained_values
        return out
