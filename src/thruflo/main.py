#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Provides a WSGI ``app_factory``.
"""

import logging

from thruflo.webapp import web

from urls import mapping

def app_factory(global_config, **local_conf):
    """Update config, setup logging, create ``model.db`` 
      and return a wsgi application.
    """
    
    # update config
    settings = global_config
    settings.update(local_conf)
    settings['tmpl_dirs'] = [settings['template_path']]
    
    # setup logging
    if settings['debug']:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('beaker').setLevel(logging.INFO)
        logging.getLogger('restkit').setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('beaker').setLevel(logging.WARNING)
        logging.getLogger('restkit').setLevel(logging.WARNING)
    
    
    # return webapp
    return web.WSGIApplication(mapping, settings=settings)
    

