
import os
#from jinja2 import Environment, FileSystemLoader
from common.mylogging import LOG
#from confAction import ConfAction
from  conf_globals import dispQ
#import filecmp
#from jnpr.junos import Device
#from jnpr.junos.utils.scp import SCP


class ParseNotification:
    def __init__(self, device):
        pass

    def __call__(self):
        LOG.info("Entered ParseNotification")
        global dispQ
        while True:
            # process the notification message
            config_dict = dispQ.get()
            dispQ.task_done()
            LOG.info("dequeued %s" %str(config_dict))

            """
            # Check if only the binding entries have changed, then sighup all snabb app
            # check which instance has to be killed if conf or cfg file changed
            """
            #self.parse_snabb_config(config_dict)

