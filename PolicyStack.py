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

import redis

from Logger import Logger
from Policies.IPPolicy import IPPolicy
from Policies.RecipientDomainPolicy import RecipientDomainPolicy
from Policies.RecipientPolicy import RecipientPolicy
from Policies.SaslSenderDomainPolicy import SaslSenderDomainPolicy
from Policies.SaslSenderPolicy import SaslSenderPolicy
from Policies.SenderDomainPolicy import SenderDomainPolicy
from Policies.SenderPolicy import SenderPolicy
from RedisConn import RedisConn


class PolicyStack:
    """
    This class contains the list of activated polices
    """

    def __init__(self):
        pass

    policies = []
    IsPoliciesInitiliazed = False

    @staticmethod
    def init_policys(parsed_config):
        if not PolicyStack.IsPoliciesInitiliazed:
            PolicyStack.IsPoliciesInitiliazed = True
            try:
                for policy in parsed_config.get('Policies', 'ActivePolicies').split(','):
                    if policy == 'IPPolicy':
                        PolicyStack.policies.append(IPPolicy(parsed_config))
                    elif policy == 'RecipientPolicy':
                        PolicyStack.policies.append(RecipientPolicy(parsed_config))
                    elif policy == 'RecipientDomainPolicy':
                        PolicyStack.policies.append(RecipientDomainPolicy(parsed_config))
                    elif policy == 'SenderPolicy':
                        PolicyStack.policies.append(SenderPolicy(parsed_config))
                    elif policy == 'SenderDomainPolicy':
                        PolicyStack.policies.append(SenderDomainPolicy(parsed_config))
                    elif policy == 'SaslSenderPolicy':
                        PolicyStack.policies.append(SaslSenderPolicy(parsed_config))
                    elif policy == 'SaslSenderDomainPolicy':
                        PolicyStack.policies.append(SaslSenderDomainPolicy(parsed_config))
            except Exception, e:
                Logger.log('Error In Policies Initialization %s ' % str(e))
                Logger.log('Server Shutting Down')
                exit(0)

    @staticmethod
    def check_policy(message):
        try:
            pipe = RedisConn.Redis_Slave.pipeline()
            for policy in PolicyStack.policies:
                policy.check_quota(message, pipe)

            redis_return = pipe.execute()

            for i in xrange(len(redis_return)):
                if redis_return[i] == 1L:
                    if PolicyStack.policies[i].Enforce:
                        PolicyStack.policies[i].log_quota(False)
                        return 'action=%s\n\n' % PolicyStack.policies[i].RejectMessage
                    else:
                        PolicyStack.policies[i].log_quota(False)
                        return 'action=dunno\n\n'

            pipe = RedisConn.Redis_Master.pipeline()
            for policy in PolicyStack.policies:
                policy.update_quota(pipe)

            redis_return = pipe.execute()
            for i in xrange(len(PolicyStack.policies)):
                PolicyStack.policies[i].log_quota(True, redis_return[i])
            return 'action=dunno\n\n'
        except KeyError as e:
            Logger.log('Unknown Profile :  %s ' % str(e))
            return 'action=dunno\n\n'
        except redis.exceptions.RedisError as e:
            Logger.log('Redis Error :  %s Message : %s' % (type(e), e.args))
            return 'action=dunno\n\n'
        except Exception as e:
            Logger.log('Error :  %s Message : %s' % (type(e), e.args))
            return 'action=dunno\n\n'
