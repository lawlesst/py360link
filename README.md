py360Link
=========
Python utilities for working with the 360Link XML API from Serial Solutions.  

It requires a 360Link XML API key, which is generally the site id that prefixes all Serial Solutions customer web pages, e.g. http://r123456.search.serialssolutions.com.

It's mostly repurposed code from Godmar Back's link360 utilities.  
http://code.google.com/p/link360/

You might also be interested in this overview of the 360Link API:
http://journal.code4lib.org/articles/108

Install
-------
pip install git+git://github.com/lawlesst/py360link.git

Use
---
```python
from py360link import get_sersol_data, Resolved
query = 'rft_id=info:doi/10.1016/j.neuroimage.2009.12.024'
sersol_data = get_sersol_data(query, key='yourkey')
resolved = Resolved(sersol_data)
```