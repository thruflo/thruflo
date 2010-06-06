#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tools for testing the thing.
"""

import logging
import urllib
import urllib2

from BeautifulSoup import BeautifulSoup

def relay_commit_payload():
    """Enjoyable hack that gets latest data from postbin
      and posts it on locally.
      
      Avoids having to deploy changes remotely when testing
      the post receive hook mechanism.
    """
    
    sock = urllib2.urlopen('http://www.postbin.org/p256i3')
    soup = BeautifulSoup(sock.read(), convertEntities='html')
    sock.close()
    
    pres = soup('pre')
    payload = urllib.unquote(unicode(pres[0])[5:-6])
    
    sock = urllib2.urlopen(
        'http://dev.thruflo.com/hooks/post_commit', 
        urllib.urlencode({'payload': payload})
    )
    sock.close()
    

