__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2017 Juniper Networks, Inc."

import sys
import os
from conf.callback import SnabbCallback
from mylogging import LOG
from jnpr.junos import Device as PyEzDevice
from jnpr.junos.exception import ConnectError
import random, string
from app_globals import *
from notification.notification import NotificationClient


class Device(object):

    """
    Main class to establish the connection and starting the twisted server
    """

    @property
    def user(self):
        """
        :return: the login user accessing the JET services
        """
        return self._auth_user

    @property
    def password(self):
        """
        :return: the password of user accessing the JET services
        """
        return self._auth_pwd

    @property
    def logfile(self):
        """
        :return: existing logfile object
        """
        return self._logfile

    @logfile.setter
    def logfile(self, value):
        # got an existing file that we need to close
        if (not value) and (None != self._logfile):
            rc = self._logfile.close()
            self._logfile = False
            return rc

        if sys.version < '3':
            if not isinstance(value, file):
                raise ValueError("value must be a file object")
        else:
            import io
            if not isinstance(value, io.TextIOWrapper):
                raise ValueError("value must be a file object")

        self._logfile = value
        return self._logfile

    @property
    def host(self):
        return self._host

    @property
    def mqttPort(self):
        return self._mqtt_port


    def __init__(self, host= DEFAULT_NETCONF_HOST, user=DEFAULT_USER_NAME, 
                 password=DEFAULT_PASSWORD, netconf_port = DEFAULT_NETCONF_PORT,
                 notification_port = DEFAULT_NOTIFICATION_PORT, **kvargs):
        self._host = host
        self._mqtt_port = notification_port
        self._auth_user = user
        self.opServer = None
        self.evHandle = None
        self.dev = None
        self.messageCallback = SnabbCallback(self)

    def initialize(self, *vargs, **kvargs):

        # Open NETCONF session
        self.dev = PyEzDevice(host=self._host, user=self._auth_user, gather_facts=False)

        try:
            self.dev.open()
            self.dev.close()
            self.messageCallback("startup config")

            # Open notification session
            nc = NotificationClient(device=self._host, port=self._mqtt_port)
            self.evHandle = nc.get_notification_service()
            cutopic = self.evHandle.create_config_update_topic()
            self.evHandle.Subscribe(cutopic, self.messageCallback)
            # subscription completed
            LOG.info("Notification channel opened now")
            self.connected = True

        except ConnectError as err:
            print("Cannot connect to device: {0}".format(err))
            sys.exit(1)

        except Exception as e:
            print("Exception received: %s" %e.message)
            sys.exit(0)

    def close(self):
        self.evHandle.Unsubscribe()
        self.connected = False
