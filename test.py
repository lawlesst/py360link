"""
Tests for handling OpenURLs with 360Link.

For these to run, a Serial Solutions 360Link XML API key must be
supplied.
"""

from pprint import pprint
import unittest
import urlparse
from py360link import get_sersol_data, Resolved

#A 360Link API key needs to be specified here.  
KEY = None

class TestPmidLookup(unittest.TestCase):
    """
    Test a simple lookup by Pubmed ID.
    """
    def setUp(self):
        ourl = 'id=pmid:19282400&sid=Entrez:PubMed'
        data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(data)
    
    def test_link_groups(self):
        """
        These will depend from institution to institution so just check for keys.
        """
        link_groups = self.sersol.link_groups
        required = ['url', 'holdingData', 'type']
        for link in link_groups:
            for req in required:
                self.assertTrue(link.has_key(req))
    
    def test_citation(self):
        citation = self.sersol.citation
        self.assertEqual(citation['creator'], 'Moriya, T')
        self.assertEqual(citation['doi'], '10.1177/1753193408098482')
        self.assertEqual(citation['volume'], '34')
        self.assertEqual(citation['spage'], '219')
        self.assertTrue(citation['title'].rfind('Effect of triangular') > -1)
        
    def test_openurl(self):
        """
        We can round trip this to see if the original request is enhanced by
        the results of the 360Link resolution.
        """
        
        ourl = self.sersol.openurl
        ourl_dict = urlparse.parse_qs(ourl)
        self.assertEqual(ourl_dict['rft_id'], ['info:doi/10.1177/1753193408098482', 'info:pmid/19282400'])
        self.assertEqual(ourl_dict['rft.eissn'][0], '1532-2211')
        print ourl
        

class TestDoiLookup(unittest.TestCase):
    def setUp(self):
        ourl = 'rft_id=info:doi/10.1016/j.neuroimage.2009.12.024'
        data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(data)
        
    def test_citation(self):
        citation = self.sersol.citation
        self.assertEqual(citation['creator'], 'Berman, Marc G.')
        self.assertEqual(citation['doi'], '10.1016/j.neuroimage.2009.12.024')
        self.assertEqual(citation['volume'], '50')
        self.assertEqual(citation['spage'], '56')
        self.assertTrue(citation['title'].rfind('Evaluating functional localizers') > -1)
        
    def test_echoed_query(self):
        qdict = self.sersol.query_dict
        self.assertEqual(qdict['rft_id'][0], 'info:doi/10.1016/j.neuroimage.2009.12.024')
        #Basic check, these are defaults.
        self.assertEqual(qdict['url_ver'][0], 'Z39.88-2004')
        self.assertEqual(qdict['version'][0], '1.0')
        
class TestCiteLookup(unittest.TestCase):
    def setUp(self):
        ourl = 'title=Organic%20Letters&date=2008&issn=1523-7060&issue=19&spage=4155'
        self.data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(self.data)
        
    def test_citation(self):
        citation = self.sersol.citation
        self.assertEqual(citation['source'], 'Organic letters')
        self.assertEqual(citation['date'], '2008')
        
    def test_echoed_query(self): 
        qdict = self.sersol.query_dict
        self.assertEqual(qdict['title'][0], 'Organic Letters')
        self.assertEqual(qdict['date'][0], '2008')
        
    def test_openurl(self):
        """
        Check for the enhanced data.
        """
        ourl = self.sersol.openurl
        ourl_dict = urlparse.parse_qs(ourl)
        self.assertEqual(ourl_dict['rft.eissn'][0], '1523-7052')
        
class TestFirstSearchBookLookup(unittest.TestCase):
    def setUp(self):
        #Sample passed from OCLC
        ourl = 'sid=FirstSearch%3AWorldCat&genre=book&isbn=9780394565279&title=The+risk+pool&date=1988&aulast=Russo&aufirst=Richard&id=doi%3A&pid=%3Caccession+number%3E17803510%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3E1st+ed.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E17803510%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F17803510&rft_id=urn%3AISBN%3A9780394565279&rft.aulast=Russo&rft.aufirst=Richard&rft.btitle=The+risk+pool&rft.date=1988&rft.isbn=9780394565279&rft.place=New+York&rft.pub=Random+House&rft.edition=1st+ed.&rft.genre=book&checksum=d6c1576188e0f87ac13f4c4582382b4f&title=Brown University&linktype=openurl&detail=RBN'
        self.data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(self.data)
    
    def test_link360_resolved(self):
        citation = self.sersol.citation
        self.assertEqual(self.sersol.format, 'book')
        self.assertEqual(citation['title'], 'The risk pool')
        self.assertTrue('9780394565279' in citation['isbn'])
    
    def test_openurl(self):
        ourl = self.sersol.openurl
        ourl_dict = urlparse.parse_qs(ourl)
        self.assertTrue(ourl_dict['rfe_dat'][0], '<accessionnumber>17803510</accessionnumber>')
        #simple string find for accession number
        self.assertTrue(ourl.rfind('17803510') > -1 )
        
class TestFirstSearchArticleLookup(unittest.TestCase):
    def setUp(self):
        #Sample passed from OCLC
        ourl = 'sid=FirstSearch%3AMEDLINE&genre=article&issn=0037-9727&atitle=Serum+and+urine+chromium+as+indices+of+chromium+status+in+tannery+workers.&title=Proceedings+of+the+Society+for+Experimental+Biology+and+Medicine.+Society+for+Experimental+Biology+and+Medicine+%28New+York%2C+N.Y.%29&volume=185&issue=1&spage=16&epage=23&date=1987&aulast=Randall&aufirst=JA&sici=0037-9727%28198705%29185%3A1%3C16%3ASAUCAI%3E2.0.TX%3B2-3&id=doi%3A&pid=%3Caccession+number%3E114380499%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AMEDLINE&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E114380499%3C%2Faccessionnumber%3E&rft_id=urn%3AISSN%3A0037-9727&rft.aulast=Randall&rft.aufirst=JA&rft.atitle=Serum+and+urine+chromium+as+indices+of+chromium+status+in+tannery+workers.&rft.jtitle=Proceedings+of+the+Society+for+Experimental+Biology+and+Medicine.+Society+for+Experimental+Biology+and+Medicine+%28New+York%2C+N.Y.%29&rft.date=1987&rft.volume=185&rft.issue=1&rft.spage=16&rft.epage=23&rft.issn=0037-9727&rft.genre=article&rft.sici=0037-9727%28198705%29185%3A1%3C16%3ASAUCAI%3E2.0.TX%3B2-3&checksum=2a13709e5b9664e62d31e421f6f77c94&title=Brown University&linktype=openurl&detail=RBN'
        self.data = get_sersol_data(ourl, key=KEY)
        self.sersol = Resolved(self.data)
    
    def test_link360_resolved(self):
        pprint(self.data)
        citation = self.sersol.citation
        self.assertEqual(self.sersol.format, 'journal')
        self.assertEqual(citation['title'], 'Serum and urine chromium as indices of chromium status in tannery workers.')
        self.assertTrue('1525-1373' in citation['eissn'])
    
    def test_openurl(self):
        ourl = self.sersol.openurl
        ourl_dict = urlparse.parse_qs(ourl)
        self.assertTrue(ourl_dict['rft.genre'][0], 'article')
        self.assertTrue(ourl_dict['rfe_dat'][0], '<accessionnumber>114380499</accessionnumber>')
        #simple string find for accession number
        self.assertTrue(ourl.rfind('114380499') > -1 )
        
       
        

if __name__ == '__main__':
    unittest.main()
    
