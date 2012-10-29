"""
Types to handle.

- articles held
- articles not held
- ebooks held
- books not held
- book chapters held
- book chapters not held
- journals held (display titles and coverage ranges)
- journals not held

"""
from xml.etree.ElementTree import ElementTree
import sys
#t = py360link.fetch_bibjson('id=pmid:19282400&sid=Entrez:PubMed', key='rl3tp7zf5x')
#t = py360link.fetch_bibjson('title=science', key='rl3tp7zf5x')

ss = "{http://xml.serialssolutions.com/ns/openurl/v1.0}"
dc = "{http://purl.org/dc/elements/1.1/}"

with open(sys.argv[1], 'rt') as f:
    tree = ElementTree()
    tree.parse(f)


results = tree.findall('*/{0}result'.format(ss))
query = tree.find('*/{0}queryString'.format(ss,)).text

from bibjsontools import from_openurl

#Get a starting bibjson object to work with
this_bib = from_openurl(query)


bibs = []

class BibJSON360Link(object):

    def __init__(api_response):
        tree = ElementTree()
        self.doc = tree.parse(f)

    def fill(self, elem, key):
        d = {}
        if elem is not None:
            d[key] = elem.text
        return d

    def pull(self, elem, path, findall=False, text=False):
        if findall is True:
            if elem:
                return elem.findall(path.format(ss,dc))
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

    def make_author(self, cite):
        authors = []
        auth = {}
        auth['name'] = pull(cite, '{1}creator', text=True)
        first = pull(cite, '{0}creatorFirst', cite)
        last = pull(cite, '{0}creatorLast', cite)
        auth.update(fill(last, 'lastname'))
        auth.update(fill(first, 'firstname'))
        authors.append(auth)
        return authors

    def make_journal(self, cite):
        jrnl = {}
        jrnl['name'] = pull(cite, '{1}source').text

        #identifiers
        issns = pull(cite, '{0}issn', findall=True)
        ids = []
        for issn in issns:
            itype = issn.attrib.get('type')
            this_id = {}
            this_id['id'] = issn.text
            if itype == 'print':
                this_id['type'] = 'issn'
            elif itype == 'electronic':
                this_id['type'] = 'eissn'
            ids.append(this_id)
        jrnl['identifier'] = ids
        return jrnl

    def make_links(link_groups):

        if link_groups is None:
            return 

        links = []
        #Holder so we don't add duplicates.
        seen_links = []
        seen_providers = []

        groups = pull(link_groups, '{0}linkGroup', findall=True)
        for group in link_groups:
            start = pull(group, '{0}holdingData/{0}startDate', text=True)
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
                if url in seen_links:
                    continue
                #print url.attrib.get('type'), url.text
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
        #sort
        #order = dict((key, idx) for idx, key in enumerate(["Elsevier", "EBSCOhost"]))
        #sorted(links, key=order.get)
        #print links
        #http://stackoverflow.com/questions/10274868/sort-a-list-of-python-dictionaries-depending-on-a-ordered-criteria
        criteria = ['JSTOR']
        def _mapped(provider):
            if provider == 'LexisNexis':
                return 20000
            elif provider == 'Elsevier':
                return -10000
            else:
                return 100

        links.sort(key=lambda x: criteria.index(x['provider']) if x['provider'] in criteria else _mapped(x['provider']))
        return links



    def make_article_identifiers(cite):
        ids = []
        #doi
        k = {'type': None,
            'id': None}
        doi = pull(cite, '{0}doi')
        if doi is not None:
            k['type'] = 'doi'
            k['id'] = doi.text
            ids.append(k)
        #pmid
        k = {}
        pmid = pull(cite, '{0}pmid')
        if pmid is not None:
            k['type'] = 'pmid'
            k['id'] = pmid.text
            ids.append(k)

        return ids

    def get_article_citation(cite, link_groups):
        b = {}
        #Handle objects first.
        #authors
        auth = make_author(cite)
        b['author'] = auth
        #journal
        jrnl = make_journal(cite)
        b['journal'] = jrnl
        #links
        b['links'] = make_links(link_groups)

        #article identifiers
        article_ids = make_article_identifiers(cite)
        b['identifier'] = article_ids

        #simple meta
        #title
        b['title'] = pull(cite, '{1}title', text=True)
        b['volume'] = pull(cite, '{0}volume', text=True)
        b['issue'] = pull(cite, '{0}issue', text=True)
        b['start_page'] = pull(cite, '{0}spage', text=True)
        #Serials Solutions doesn't return end pages
        #so we will set all articles to EOA for 'end of article'.
        b['end_page'] = 'EOA'

        #year
        year_elm = pull(cite, '{1}date')
        if year_elm is not None:
            b['year'] = year_elm.text.split('-')[0]
        return b



for res in results:

    format = res.attrib.get('format')

    #One citation per result
    citation = pull(res, '{0}citation')
    #One linkGroup with many linkGroups.
    link_groups = pull(res, '{0}linkGroups')
    title = pull(citation, '{1}title', text=True)
    source = pull(citation, '{1}source', text=True)
    if format == 'journal':
        if (source is not None) and (title is None):
            btype = 'journal'
            links = make_links(link_groups)
            jrnl = make_journal(citation)
            for ids in this_bib.get('identifier', []):
                jrnl['identifier'].append(ids)
            this_bib['journal'] = jrnl
            this_bib['type'] = btype
        else:
            btype ='article'
            bibj = get_article_citation(citation, link_groups)
            print bibj['title']
            for link in bibj.get('links', []):
                if link['type'] == 'article':
                    print link['provider']
            bibs.append(bibj)
    elif format == 'book':
        #Test for chapter.
        title = pull(citation, '{1}title', text=True)
        source = pull(citation, '{1}source', text=True)
        if (source is not None) and (source != title):
            btype = 'bookitem'
        else:
            btype = 'book'
    else:
        print 'UNKNOWN'

    print title, source
    print btype
    print '---\n'

from pprint import pprint
pprint(this_bib)


    # journal = citation.find('{1}source'.format(ss,dc)).text 
    # issn = citation.find('{0}issn'.format(ss,dc))
    # if issn is not None:
    #     issn_type = issn.attrib.get('type')
    #     issn_value = issn.text
    #     print issn_type, issn_value

    # #linkGroups
    # groups = linkGroups.findall('{0}linkGroup'.format(ss,dc))
    # for group in groups:
    #     #holding = group.findall('{0}holdingData'.format(ss,dc))
    #     start = group.find('{0}holdingData/{0}startDate'.format(ss,dc))
    #     provider = group.find('{0}holdingData/{0}providerName'.format(ss,dc)).text
    #     print provider
    #     if start is not None:
    #         print start.text
    #     urls = group.findall('{0}url'.format(ss,dc))
    #     for url in urls:
    #         print url.attrib.get('type'), url.text
    # print '----\n'

# print results
# print '--'

# citations = t.findall('*/{0}result/{0}citation'.format(ss,))
# linkgroups = t.findall('*/{0}result/{0}linkGroups'.format(ss,))

# print citations
# print '--'
# print linkgroups
#print resp
#print t.findall('{0}openURLResponse/{0}result'.format(ns,))

