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

import bsddb

from Logger import Logger
from RedisConn import RedisConn


class HashLookup:
    """
    Provides Hash File Lookup
    """

    def lookup(self, key, ttl):
        profile = None
        if ttl != 0:
            profile = RedisConn.Redis_Slave.get('HashLookupProfile_' + key)
        if profile is None:
            try:
                profile = bsddb.hashopen(self.dbfile, "r").get(key, 'default').lower()
                if ttl != 0:
                    RedisConn.Redis_Master.setex('HashLookupProfile_' + key, profile, ttl)
            except Exception as e:
                Logger.log('HashLookup Error :  %s Message : %s' % (type(e), e.args))
                profile = 'default'
        return profile

    def __init__(self, dbfile):
        self.dbfile = dbfile
