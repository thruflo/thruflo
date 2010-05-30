#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Python clients to external service APIs.
"""

import config

# patch github library to use https by default
import github2.request
github2.request.GITHUB_URL = "https://github.com"
github2.request.URL_PREFIX = "https://github.com/api/v2/json"

from github2.client import Github
from github2.request import GithubError

# provide github client factory
# @@ ...

# provide ``spreedly`` client
from dependencies.spreedly import Spreedly
spreedly = Spreedly(
    site=config.spreedly['site_name'], 
    base_url=config.spreedly['spreedly_base_url'], 
    token=config.spreedly['spreedly_token']
)
