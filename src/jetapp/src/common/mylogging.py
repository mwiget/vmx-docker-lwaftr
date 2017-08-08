__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2017 Juniper Networks, Inc."

import logging
from logging.handlers import RotatingFileHandler

# Logging Parameters
DEFAULT_LOG_FILENAME = '/tmp/jetapp.log'
DEFAULT_LOG_LEVEL = logging.INFO


# Enable Logging to a file
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s ] %(message)s"
rotation_handler = logging.handlers.RotatingFileHandler(filename=DEFAULT_LOG_FILENAME, maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotation_handler.setFormatter(formatter)
rotation_handler.setLevel(DEFAULT_LOG_LEVEL)

LOG = logging.getLogger('snabbVMXJET')
LOG.setLevel(DEFAULT_LOG_LEVEL)
LOG.addHandler(rotation_handler)
