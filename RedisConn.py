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

from sys import exit

from Logger import Logger

try:
    import redis
except Exception as e:
    Logger.log('Error Importing Redis Python Lib %s ' % str(e))
    Logger.log('Server Shutting Down')
    exit(0)


class RedisConn(object):
    """
    This class sets up connections to Redis
    """
    LUA_CHECK_LIMIT = '''
    if redis.call("EXISTS",KEYS[1]) == 1 
    then                                                                                                             
        local cnt = redis.call('GET', KEYS[1])
        if cnt + 1 > tonumber(ARGV[1])
        then
            return 1
        end 
        return 0
    else
        return 0
    end
    '''

    LUA_INCR = '''
    local cnt = redis.call('INCR', KEYS[1])
    if cnt == 1
    then
        redis.call('EXPIRE', KEYS[1], ARGV[1])
    end
    return cnt
    '''

    LUA_DO_NOTHING = '''
    return -1
    '''

    Redis_Master = Redis_Slave = LUA_CALL_INCR = LUA_CALL_CHECK_LIMIT = None
    LUA_CALL_DO_NOTHING_SLAVE = LUA_CALL_DO_NOTHING_MASTER = None

    @staticmethod
    def init_redis(parsed_config):
        try:
            redismasterpass = parsed_config.get('RedisConfig', 'RedisMasterAuth')
            if redismasterpass == 'None':
                redismasterpass = None
            redisslavepass = parsed_config.get('RedisConfig', 'RedisSlaveAuth')
            if redisslavepass == 'None':
                redisslavepass = None
            RedisConn.Redis_Master = redis.Redis(host=parsed_config.get('RedisConfig', 'RedisMasterHost'),
                                                 port=parsed_config.getint('RedisConfig', 'RedisMasterPort'),
                                                 password=redismasterpass,
                                                 db=parsed_config.getint('RedisConfig', 'RedisMasterDB'))
            RedisConn.Redis_Slave = redis.Redis(host=parsed_config.get('RedisConfig', 'RedisSlaveHost'),
                                                port=parsed_config.getint('RedisConfig', 'RedisSlavePort'),
                                                password=redisslavepass,
                                                db=parsed_config.getint('RedisConfig', 'RedisSlaveDB'))
            RedisConn.LUA_CALL_INCR = RedisConn.Redis_Master.register_script(RedisConn.LUA_INCR)
            RedisConn.LUA_CALL_CHECK_LIMIT = RedisConn.Redis_Slave.register_script(RedisConn.LUA_CHECK_LIMIT)
            RedisConn.LUA_CALL_DO_NOTHING_SLAVE = RedisConn.Redis_Slave.register_script(RedisConn.LUA_DO_NOTHING)
            RedisConn.LUA_CALL_DO_NOTHING_MASTER = RedisConn.Redis_Slave.register_script(RedisConn.LUA_DO_NOTHING)
        except Exception, E:
            Logger.log('Server Shutting Down')
            Logger.log(str(E))
            exit(0)
