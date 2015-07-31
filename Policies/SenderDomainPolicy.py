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
from ProfileLookup import ProfileLookup
from RedisConn import RedisConn


class SenderDomainPolicy:
    """
    This class provides sender Domain rate limiting
    """
    key = 'sender'
    prefix = 'SenderDomainPolicy_'
    quota = {}

    def __init__(self, parsed_config):
        self.parsed_config = parsed_config
        self.Enforce = parsed_config.getboolean('SenderDomainPolicy', 'Enforce')
        self.RejectMessage = parsed_config.get('SenderDomainPolicy', 'RejectMessage')
        self.ProfileLookupObj = ProfileLookup.create_profile_lookup('SenderDomainPolicy', parsed_config)
        self.ProfileCacheTTL = parsed_config.getint('SenderDomainPolicy', 'ProfileCacheTime')
        for i in parsed_config.items('SenderDomainPolicy-Profiles'):
            limits = i[1].split(',')
            profile = i[0].lower()
            SenderDomainPolicy.quota[profile] = (int(limits[0]), int(limits[1]))
        self.value = self.profile = self.error = None

    def check_quota(self, message, redis_pipe):
        self.error = False
        try:
            self.value = message.data[self.key].split('@')[1].lower()
            self.profile = self.ProfileLookupObj.lookup(self.value, self.ProfileCacheTTL)
            RedisConn.LUA_CALL_CHECK_LIMIT(keys=[SenderDomainPolicy.prefix + self.value],
                                           args=[SenderDomainPolicy.quota[self.profile][0]], client=redis_pipe)
        except IndexError:
            self.error = True
            RedisConn.LUA_CALL_DO_NOTHING_SLAVE(keys=[], args=[], client=redis_pipe)

    def update_quota(self, redis_pipe):
        if self.error:
            RedisConn.LUA_CALL_DO_NOTHING_MASTER(keys=[], args=[], client=redis_pipe)
        else:
            RedisConn.LUA_CALL_INCR(keys=[SenderDomainPolicy.prefix + self.value],
                                    args=[SenderDomainPolicy.quota[self.profile][1]], client=redis_pipe)

    def log_quota(self, message, accept, redis_val=None):
        if accept:
            if self.error:
                Logger.log('SenderDomainPolicy Unable To Spilt Sender (%s) Action: accept' % (message.data[self.key]))
            else:
                Logger.log('SenderDomainPolicy SenderDomain: %s Quota: (%s/%s) Profile: %s Action: accept' % (
                    self.value, str(int(redis_val)), str(SenderDomainPolicy.quota[self.profile][0]), self.profile))
        else:
            Logger.log('SenderDomainPolicy SenderDomain: %s Quota: Exceeded Profile: %s Action: reject' % (
                self.value, self.profile))
