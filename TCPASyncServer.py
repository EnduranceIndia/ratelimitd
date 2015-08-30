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

import asyncore
import socket
import asynchat

from Daemon import Daemon
from PostfixParser import PostfixParser
from PolicyStack import PolicyStack
from Logger import Logger


class Server(asyncore.dispatcher):
    def __init__(self, host, port, parsed_config):
        self.parsed_config = parsed_config
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(1)

    def handle_accept(self):
        tcpsocket, address = self.accept()
        TCPHandler(tcpsocket, self.parsed_config)


class TCPHandler(asynchat.async_chat):
    def __init__(self, sock, parsed_config):
        self.parsed_config = parsed_config
        asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator('\n\n')
        self.buffer = []

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        message = PostfixParser(self.buffer)
        self.push(PolicyStack.check_policy(message))
        self.buffer = []


class TCPASyncServer(Daemon):
    """
    This class sets up a TCP Async Server
    """

    def __init__(self, parsed_config):
        """
        Constructor
        """
        try:
            self.parsed_config = parsed_config
            PolicyStack.init_policys(self.parsed_config)
            Daemon.__init__(self, parsed_config.get('Server', 'PidFile'))
            self.Host = parsed_config.get('Server', 'Host')
            self.Port = parsed_config.getint('Server', 'Port')
        except Exception, e:
            Logger.log(str(e))
            Logger.log('Server Shutting Down')
            exit(1)

    def run(self):
        try:
            Server(self.Host, self.Port, self.parsed_config)
            asyncore.loop(use_poll=True)
        except Exception, e:
            Logger.log(str(e))
            Logger.log('Server Shutting Down')
            exit(1)
