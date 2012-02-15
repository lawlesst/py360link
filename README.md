py360Link
=========
This is a Python based utility module for woking with the 360Link XML API from Serial Solutions.  

It requires a 360Link XML API key, which is generally the site id that prefixes all Serial Solutions customer web pages, e.g. http://r123456.search.serialssolutions.com.

It's mostly repurposed code from Godmar Back's link360 utilities.  
http://code.google.com/p/link360/

You might also be interested in this overview of the 360Link API:
http://journal.code4lib.org/articles/108

```python
from pylink360 import get_sersol_data, Resolve
query = 'rft_id=info:doi/10.1016/j.neuroimage.2009.12.024'
sersol_data = get_sersol_data(query, key='yourkey')
resolved = Resolve(sersol_data)
```