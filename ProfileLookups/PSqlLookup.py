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
from Logger import Logger
from RedisConn import RedisConn

try:
    import psycopg2
except Exception as e:
    Logger.log('Error Importing psycopg2 Python Lib %s ' % str(e))
    Logger.log('Server Shutting Down')
    exit(1)


class PSqlLookup:
    """
    Provides PostgresSQL Lookup
    """

    def __init__(self, uri, query):
        self.query = query
        self.uri = uri

    def lookup(self, key, ttl):
        profile = None
        if ttl != 0:
            profile = RedisConn.Redis_Slave.get('PSqlLookupProfile_' + key)
        if profile is None:
            try:
                conn = psycopg2.connect(self.uri)
                cur = conn.cursor()
                cur.execute(self.query.replace('%s', key))
                profile = cur.fetchone()
                if profile is None:
                    Logger.log(
                        'PSqlLookup Error :  %s Message : %s' % ('DB Lookup Error', 'DB Call Returned Empty Result'))
                    profile = 'default'
                else:
                    profile = profile[0].lower()
                    if ttl != 0:
                        RedisConn.Redis_Master.setex('PSqlLookupProfile_' + key, profile, ttl)
            except Exception as e:
                Logger.log('PSqlLookup Error :  %s Message : %s' % (type(e), e.args))
                profile = 'default'
        return profile
