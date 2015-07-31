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


class SaslSenderPolicy:
    """
    This class provides saslsender rate limiting
    """
    key = 'sasl_sender'
    prefix = 'SaslSenderPolicy_'
    quota = {}

    def __init__(self, parsed_config):
        self.parsed_config = parsed_config
        self.Enforce = parsed_config.getboolean('SaslSenderPolicy', 'Enforce')
        self.RejectMessage = parsed_config.get('SaslSenderPolicy', 'RejectMessage')
        self.ProfileLookupObj = ProfileLookup.create_profile_lookup('SaslSenderPolicy', parsed_config)
        self.ProfileCacheTTL = parsed_config.getint('SaslSenderPolicy', 'ProfileCacheTime')
        for i in parsed_config.items('SaslSenderPolicy-Profiles'):
            limits = i[1].split(',')
            profile = i[0].lower()
            SaslSenderPolicy.quota[profile] = (int(limits[0]), int(limits[1]))
        self.value = self.profile = self.error = None

    def check_quota(self, message, redis_pipe):
        self.value = message.data[self.key].lower()
        self.error = False
        if self.value != '':
            self.profile = self.ProfileLookupObj.lookup(self.value, self.ProfileCacheTTL)
            RedisConn.LUA_CALL_CHECK_LIMIT(keys=[SaslSenderPolicy.prefix + self.value],
                                           args=[SaslSenderPolicy.quota[self.profile][0]], client=redis_pipe)
        else:
            self.error = True
            RedisConn.LUA_CALL_DO_NOTHING_SLAVE(keys=[], args=[], client=redis_pipe)

    def update_quota(self, redis_pipe):
        if self.error:
            RedisConn.LUA_CALL_DO_NOTHING_MASTER(keys=[], args=[], client=redis_pipe)
        else:
            RedisConn.LUA_CALL_INCR(keys=[SaslSenderPolicy.prefix + self.value],
                                    args=[SaslSenderPolicy.quota[self.profile][1]], client=redis_pipe)

    def log_quota(self, accept, redis_val=None):
        if accept:
            if self.error:
                Logger.log('SaslSenderPolicy SaslSender: NullSaslSender Action: accept')
            else:
                Logger.log('SaslSenderPolicy SaslSender: %s Quota: (%s/%s) Profile: %s Action: accept' % (
                    self.value, str(int(redis_val)), str(SaslSenderPolicy.quota[self.profile][0]), self.profile))
        else:
            Logger.log('SaslSenderPolicy SaslSender: %s Quota: Exceeded Profile: %s Action: reject' % (
                self.value, self.profile))
