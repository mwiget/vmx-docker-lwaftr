__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2017 Juniper Networks, Inc."

from mylogging import LOG
import op.protos.mgd_service_pb2 as mgd_service_pb2
import op.protos.openconfig_service_pb2 as openconfig_service_pb2
import common.app_globals


class Sanity(object):
    """
    Contains the sanity functions for the JET app
    """
    def __init__(self, dev):
        self._dev = dev
        LOG.info("Sanity object initialized")

    def YangModulePresent(self):
        # Check if the YANG modules are present on the device
        # Use the MGD api to get the YANG config
        yang_config_present = True
        stub = mgd_service_pb2.beta_create_ManagementRpcApi_stub(self._dev.getChannel())
        try:
            request = mgd_service_pb2.ExecuteOpCommandRequest(
                xml_command="<get-system-yang-packages></get-system-yang-packages>",
                out_format=0, request_id=1000)
            for response in stub.ExecuteOpCommand(request, common.app_globals.RPC_TIMEOUT_SECONDS):
                LOG.info("Invoked the OpCommand to fetch yang packages, received response: %s" %response)
                if "ietf-inet-types.yang" in response.data and "ietf-softwire.yang" in response.data:
                    yang_config_present = True

        except Exception as e:
            LOG.error("Failed to execute the MGD api due to exception: %s" %e.message)

        return yang_config_present


    def NotificationConfigPresent(self):
        # Check if the commit notification config is present
        try:
            stub = openconfig_service_pb2.beta_create_OpenconfigRpcApi_stub(self._dev.getChannel())
            getRequest = openconfig_service_pb2.GetRequestList(operation_id="1001", operation=1,
                                                               path="/configuration/system/services/extension-service/notification")
            request = openconfig_service_pb2.GetRequest(request_id=1002, encoding=0, get_request=[getRequest])
            response = stub.Get(request, common.app_globals.RPC_TIMEOUT_SECONDS)
            print response
            for rsp in response.response:
                if rsp.response_code == openconfig_service_pb2.OK and rsp.value != "":
                    LOG.info("Invoked the getRequest for notification configuration, response= %s" % rsp.message)
                    return True
            LOG.info("Notification configuration is not present")

        except Exception as e:
            LOG.error("Failed to fetch notification configuration due to exception: %s" %e.message)
        return False

    def CommitNotificationConfig(self):
        # Apply the commit notification config
        jsonCfgValue = """ <configuration-json>
        {
            "configuration" : {
                "system" : {
                    "services" : {
                        "extension-service" : {
                            "notification" : {
                                "max-connections" : "5",
                                "allow-clients" : {
                                    "address" : ["0.0.0.0/0"]
                                }
                            }
                        }
                    }
                }
            }
        }</configuration-json> """

        try:
            stub = openconfig_service_pb2.beta_create_OpenconfigRpcApi_stub(self._dev.getChannel())
            jsonCfgRequest = openconfig_service_pb2.SetRequest.ConfigOperationList(operation_id="jcfg", operation=0,
                                                                                   path="/", value=jsonCfgValue)
            request = openconfig_service_pb2.SetRequest(request_id=1000, encoding=1, config_operation=[jsonCfgRequest])
            response = stub.Set(request, common.app_globals.RPC_TIMEOUT_SECONDS)
            LOG.info("Applied the notification config, response:%s" %response)
            return True

        except Exception as e:
            LOG.error("Failed to set the notification config, execption: %s" % e.message)
            return False
