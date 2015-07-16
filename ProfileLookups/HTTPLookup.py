"""
Copyright 2015 Sai Gopal

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import urllib

from Logger import Logger
from RedisConn import RedisConn


class HTTPLookup:
    """
    Provides HTTP Lookup
    """

    def lookup(self, key, ttl):
        profile = None
        if ttl != 0:
            profile = RedisConn.Redis_Slave.get('HTTPLookupProfile_' + key)
        if profile is None:
            try:
                profile = urllib.urlopen(self.url.replace('%s', key)).read()
                if ttl != 0:
                    RedisConn.Redis_Master.setex('HTTPLookupProfile_' + key, profile, ttl)
            except Exception as e:
                Logger.log('HTTPLookup Error :  %s Message : %s' % (type(e), e.args))
                profile = 'default'
        return profile

    def __init__(self, url):
        self.url = url
