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

from syslog import openlog, LOG_MAIL, LOG_PID, syslog
from sys import argv


class Logger(object):
    """
    This class is responsible for logging
    """

    @staticmethod
    def openlog():
        openlog(argv[0], LOG_PID, LOG_MAIL)

    @staticmethod
    def log(message):
        syslog(message)
