__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2017 Juniper Networks, Inc."

import logging
import sys
#from logging.handlers import RotatingFileHandler

# Logging Parameters
#DEFAULT_LOG_FILENAME = '/tmp/jetapp.log'
DEFAULT_LOG_LEVEL = logging.DEBUG

# Enable Logging to a file
#FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s ] %(message)s"
#rotation_handler = logging.handlers.RotatingFileHandler(filename=DEFAULT_LOG_FILENAME, maxBytes=100000, backupCount=5)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#rotation_handler.setFormatter(formatter)
#rotation_handler.setLevel(DEFAULT_LOG_LEVEL)

# Enable logging to stdout
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.DEBUG)
console.setFormatter(formatter)

LOG = logging.getLogger('snabbVMXJET')
LOG.setLevel(DEFAULT_LOG_LEVEL)
LOG.addHandler(console)
