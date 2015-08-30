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

import ConfigParser
import sys

from Logger import Logger
from TCPASyncServer import TCPASyncServer
from RedisConn import RedisConn


class Ratelimitd(object):
    """
    This class is responsible to start the entire app
    """

    def __init__(self, config_path):
        """
        Constructor
        """
        self.Config = ConfigParser.ConfigParser()
        self.Config.read(config_path)
        Logger.openlog()
        self.Server = TCPASyncServer(self.Config)
        RedisConn.init_redis(self.Config)

    def run(self, argv):
        if len(argv) == 2:
            if 'start' == argv[1]:
                self.Server.start()
            elif 'stop' == argv[1]:
                self.Server.stop()
            elif 'restart' == argv[1]:
                self.Server.restart()
            else:
                print "Unknown command"
                sys.exit(2)
            sys.exit(1)
        else:
            print "usage: %s start|stop|restart" % sys.argv[0]
            sys.exit(2)


if __name__ == '__main__':
    App = Ratelimitd('/opt/ratelimitd/etc/ratelimitd.conf')
    App.run(sys.argv)
