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

# with open(sys.argv[1], 'rt') as f:
#     tree = ElementTree()
#     tree.parse(f)


# results = tree.findall('*/{0}result'.format(ss))
# query = tree.find('*/{0}queryString'.format(ss,)).text

def pull(elem, path, findall=False, text=False):
    """
    XML parsing helper.
    """
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

def sort_links(links):
    """
    Sort the links returned by library defined criteria.
    http://stackoverflow.com/questions/10274868/sort-a-list-of-python-dictionaries-depending-on-a-ordered-criteria

    A high value will push the link to the bottom of the list.
    A low or negative value will bring it to the front.
    """
    criteria = ['JSTOR']
    def _mapped(provider):
        if provider == 'LexisNexis':
            return 20000
        elif provider == 'Elsevier':
            return -10000
        else:
            return 100
    links.sort(key=lambda x: criteria.index(x['provider'])\
             if x['provider'] in criteria\
             else _mapped(x['provider']))
    return links

class Bib(object):

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
                btype ='article'
        elif format == 'book':
            #Test for chapter.
            if (source is not None) and (source != title):
                btype = 'book chapter'
            else:
                btype = 'book'
        return btype

    def get_identifiers(self):
        """
        Get a list of identifiers for a given citation.
        """
        cite = self.citation
        #Get potential identifiers
        ids = [
            {
                'type': 'doi',
                'id': pull(cite, '{0}doi', text=True)
            },
            {
                'type': 'pmid',
                'id': pull(cite, '{0}pmid', text=True)
            },
            {
                'type': 'isbn',
                'id': pull(cite, '{0}isbn', text=True)
            },
        ]
        ids = filter(lambda id: id['id'] is not None, ids)
        return ids

    def get_author(self):
        cite = self.citation
        authors = []
        auth = {}
        auth['name'] = pull(cite, '{1}creator', text=True)
        first = pull(cite, '{0}creatorFirst', cite, text=True)
        last = pull(cite, '{0}creatorLast', cite, text=True)
        auth['lastname'] = last
        auth['firstname'] = first
        authors.append(auth)
        return authors

    def get_common(self):
        """
        Pull metdata common to all bytpes.
        """
        cite = self.citation
        bib = {}
        #title and author are the same for all fromats in bibjson
        bib['title'] = self.title
        if self.btype == 'book chapter':
            bib['booktitle'] = self.source
        bib['author'] = self.get_author()
        bib['start_page'] = pull(cite, '{0}spage', text=True)
        year = pull(cite, '{1}date', text=True)
        if year is not None:
            bib['year'] = year.split('-')[0]
        bib['issue'] = pull(cite, '{0}issue', text=True)
        bib['volume'] = pull(cite, '{0}volume', text=True)
        bib['publisher'] = pull(cite, '{1}publisher', text=True)
        bib['address'] = pull(cite, '{0}publicationPlace', text=True)
        return bib


    def get_links(self, sort=False, remove_duplicates=True, article_only=True):
        #One linkGroup with many linkGroups.
        link_groups = pull(self.item, '{0}linkGroups')
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
                    if article_only is True:
                        break
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
            return sort_links(links)
        return links

    def convert(self):
        """
        Make BibJSON from this result.
        """
        b = {}
        b['bul-type'] = self.btype
        b.update(self.get_common())
        b['links'] = self.get_links()
        b['identifiers'] = self.get_identifiers()
        return b


class Link360Response(object):

    def __init__(self, api_response):
        tree = ElementTree()
        self.tree = tree.parse(api_response)

    def results(self):
        results = self.tree.findall('*/{0}result'.format(ss))
        return results

    def query(self):
        """
        Get the raw query from the SerSol response.
        """
        query = self.tree.find('*/{0}queryString'.format(ss,)).text
        return query

    def library(self):
        """
        Get the library name from the response.
        """
        lib = self.tree.find('*/{0}library/{0}name'.format(ss,)).text
        return lib

    def library_id(self):
        """
        Get the code associated with the library.
        """
        lib = self.tree.find('*/{0}library'.format(ss,))
        code = lib.attrib.get('id')
        return code


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



# for res in results:

#     format = res.attrib.get('format')

#     #One citation per result
#     citation = pull(res, '{0}citation')
#     #One linkGroup with many linkGroups.
#     link_groups = pull(res, '{0}linkGroups')
#     title = pull(citation, '{1}title', text=True)
#     source = pull(citation, '{1}source', text=True)


#     print title, source
#     print btype
#     print '---\n'

# from pprint import pprint
# pprint(this_bib)


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

