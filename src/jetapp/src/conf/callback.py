__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2015 Juniper Networks, Inc."

from common.mylogging import LOG
from conf_globals import dispQ as dispQ
from jnpr.junos import Device
import os
import common.app_globals


class SnabbCallback:
    def __init__(self, dev):
        self._dev = dev

    def __call__(self, message):
        global dispQ
        LOG.info("Inside Handle commit notifications")
        LOG.info("Received message: %s" % str(message))
        try:
            # Push all the configuration into a new file
            LOG.info("push all the config into a new file")
            self._dev.dev.open()
            config_dict = self._dev.dev.rpc.get_config(filter_xml='softwire-config', model='ietf',
                                                  namespace="urn:ietf:params:xml:ns:yang:ietf-softwire", options={'format': 'json'})
            LOG.info("get_config successful")
            dispQ.put(config_dict['ietf-softwire:softwire-config'])

        except Exception as e:
            LOG.critical("Exception: %s" % e.message)
            LOG.info('Exiting the JET app')
            os._exit(1)
        return
