__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2017 Juniper Networks, Inc."

import sys
import os
#from jnpr.jet.JetHandler import *
from sanity import Sanity
from conf.callback import SnabbCallback
from mylogging import LOG
from grpc.beta import implementations
import op.protos.authentication_service_pb2 as authentication_service_pb2
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


    def establish_connection(self):
        LOG.info("Connected to JSD:ip=%s, port=%s, client-id = %s" %(self._host, self._rpc_port, self._client_id))
        channel = implementations.insecure_channel(self._host, self._rpc_port)
        stub = authentication_service_pb2.beta_create_Login_stub(channel)
        request = authentication_service_pb2.LoginRequest(user_name=self._auth_user, password= self._auth_pwd,
                                                          client_id=self._client_id)
        login_response = stub.LoginCheck(request, RPC_TIMEOUT_SECONDS)
        LOG.info("Received response from the LoginCheck: %s" %login_response.result)
        return channel

    def __init__(self, host= DEFAULT_RPC_HOST, user=DEFAULT_USER_NAME, pwd=DEFAULT_PASSWORD,
                 rpc_port=DEFAULT_RPC_PORT, notification_port = DEFAULT_NOTIFICATION_PORT, **kvargs):
        self._host = host
        self._mqtt_port = notification_port
        self._auth_user = user
        self._auth_pwd = pwd
        self._rpc_port = rpc_port
        # Creating a random client id everytime to avoid disconnect from JSD
        self._client_id =  ''.join(random.choice(string.lowercase) for i in range(10))
        self._rpc_channel = self.establish_connection()
        # Initialize the instance variables
        self.connected = False
        self.opServer = None
        self.evHandle = None
        self.messageCallback = SnabbCallback(self)

    def initialize(self, *vargs, **kvargs):
        # Create a request response session
        try:
            sanityObj = Sanity(self)
            sanityResult = sanityObj.YangModulePresent()
            if False == sanityResult:
                # log the message
                LOG.critical("Yang module not present")
                sys.exit(0)
            LOG.info("YANG module present")

            sanityResult = sanityObj.NotificationConfigPresent()
            if (True == sanityResult):
                # Apply the commit notification config of the vmx
                print("Commit notification config is not present")
                result = sanityObj.CommitNotificationConfig()
                if (False == result):
                    # Failed to apply the notification config on the vmx
                    LOG.critical("Failed to apply commit notification config on the VMX")
                    # log the message
                    sys.exit(0)
                else:
                    LOG.info("Applied the commit notification config successfully")
            else:
                # log that Notification config is present
                LOG.info("Commit Notification config already present")
                pass

            # Open notification session

            nc = NotificationClient(device=self._host, port=self._mqtt_port)
            self.evHandle = nc.get_notification_service()
            cutopic = self.evHandle.create_config_update_topic()
            self.evHandle.Subscribe(cutopic, self.messageCallback)
            # subscription completed
            LOG.info("Notification channel opened now")
            self.connected = True
            LOG.info('Device is initialized now')
        except Exception as e:
            print("Exception received: %s" %e.message)
            sys.exit(0)

    def getChannel(self):
        if self._rpc_channel:
            return self._rpc_channel
        else:
            return self.establish_connection()

    def close(self):
        self.evHandle.Unsubscribe()
        self.connected = False