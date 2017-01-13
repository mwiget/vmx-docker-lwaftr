import collections
import paho
import struct
from notification_handler import *
from common.app_globals import *
from common.mylogging import LOG

class NotificationClient:

    def __init__(self, device=DEFAULT_USER_NAME, port=DEFAULT_NOTIFICATION_PORT,
                user=None, password=None, tls=None, keepalive=DEFAULT_MQTT_TIMEOUT,
                bind_address="", is_stream=False):
        """
        Create a request response session with the  JET server. Raises exception in case
        of invalid arguments or when JET notification server is not accessible.

        @param device: JET Server IP address. Default is localhost
        @param port: JET Notification port number. Default is 1883
        @param user: Username on the JET server, used for authentication and authorization.
        @param password: Password to access the JET server, used for authentication and authorization.
        @param keepalive: Maximum period in seconds between communications with the broker. Default is 60.
        @param bind_address: Client source address to bind. Can be used to control access at broker side.

        @return: JET Notification object.
        """

        try:
            self.notifier = NotifierMqtt()
            LOG.info('Connecting to JET notification server')
            self.notifier.mqtt_client.connect(device, port, keepalive, bind_address)
            self.notifier.mqtt_client.loop_start()
            self.notifier.handlers = collections.defaultdict(set)
            if is_stream == True:
                self.notifier.mqtt_client.on_message = self.notifier.on_stream_message_cb
            else:
                self.notifier.mqtt_client.on_message = self.notifier.on_message_cb

        except struct.error as err:
            message = err.message
            err.message = 'Invalid argument value passed in %s at line no. %s\nError: %s' \
                          % (traceback.extract_stack()[0][0], traceback.extract_stack()[0][1], message)
            LOG.error('%s' % (err.message))
            raise err
        except Exception, tx:
            tx.message = 'Could not connect to the JET notification server'
            LOG.error('%s' % (tx.message))
            raise Exception(tx.message)
        pass

    def close_notification_session(self):
        """
        This method closes the JET Notification channel.

        """

        self.notifier.Close()
        LOG.info('JET notification channel closed by user.')
        pass

    def get_notification_service(self):
        """
        This method will return object that will provide access to notification
        service methods.

        """
        return self.notifier
