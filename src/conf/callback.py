__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2015 Juniper Networks, Inc."

from common.mylogging import LOG
from conf_globals import dispQ as dispQ
import os
import op.protos.openconfig_service_pb2 as openconfig_service_pb2
import common.app_globals
import json

class SnabbCallback:
    def __init__(self, dev):
        self._dev = dev

    def __call__(self, message):
        global dispQ
        LOG.info("Inside Handle commit notifications")
        LOG.info("Received message: %s" %str(message))
        config_dict = message['commit-patch']
        print config_dict
        try:
            sw_present = False
            for keys in config_dict:
                if keys.endswith('softwire-config'):
                    sw_present = True
                    break
            if sw_present:
                # Push all the configuration into a new file
                stub = openconfig_service_pb2.beta_create_OpenconfigRpcApi_stub(self._dev.getChannel())

                get_request = openconfig_service_pb2.GetRequestList(operation_id="1001", operation=1,
                                                                   path="/configuration/ietf-softwire:softwire-config")
                request = openconfig_service_pb2.GetRequest(request_id=1002, encoding=1, get_request=[get_request])
                response = stub.Get(request, common.app_globals.RPC_TIMEOUT_SECONDS)
                for rsp in response.response:
                    print rsp.value
                    if rsp.response_code == openconfig_service_pb2.OK and rsp.value != "":
                        print rsp

                        LOG.info(
                            "Invoked the getRequest for snabb configuration")
                        config_dict = json.loads(rsp.value)["ietf-softwire:softwire-config"]
                        LOG.debug("Notification message contains the config %s" %(str(config_dict)))
                        dispQ.put(config_dict)
            else:
                LOG.info("Softwire-config not present in the notification")
        except Exception as e:
            LOG.critical("Exception: %s" %e.message)
            LOG.info('Exiting the JET app')
            os._exit(1)
        return

