#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Shared helper functions.
"""

import logging
import hashlib
import random
import time
import urllib

try:
    import simplejson as json
except ImportError:
    import json

def do_nothing():
    return None


def _unicode(value):
    if isinstance(value, str):
        return value.decode("utf-8")
    assert isinstance(value, unicode)
    return value

def unicode_urlencode(params):
    if isinstance(params, dict):
        params = params.items()
    return urllib.urlencode([(
                k, 
                isinstance(v, unicode) and v.encode('utf-8') or v
            ) for k, v in params
        ]
    )


def generate_hash(algorithm='sha1', s=None):
    """Generates a random string.
    """
    
    # if a string has been provided use it, otherwise default 
    # to producing a random string
    s = s is None and '%s%s' % (random.random(), time.time()) or s
    hasher = getattr(hashlib, algorithm)
    return hasher(s).hexdigest()
    


def json_encode(value, **kwargs):
    """JSON-encodes the given Python object."""
    
    return json.dumps(value, **kwargs)
    

def json_decode(value, **kwargs):
    """Returns Python objects for the given JSON string."""
    
    return json.loads(_unicode(value), **kwargs)
    


