
import os
from jinja2 import Environment, FileSystemLoader
from common.mylogging import LOG
from conf_action import ConfAction
from  conf.conf_globals import dispQ
import filecmp
#from jnpr.junos import Device
#from jnpr.junos.utils.scp import SCP
from ftplib import FTP


class ParseNotification:
    def __init__(self, device):
        self.binding_changed = False
        self.old_cfg = None
        self.old_conf = None
        self.old_binding_filename = None
        self._dev = device
        # All the instances will be added to this list
        self.instances = {}

    def get_binding_file(self, remote_filename, local_filename):
        try:
            # Create a Pyez connection with the device
            ftp = FTP(self._dev._host)
            ftp.login(user=self._dev._auth_user, passwd=self._dev._auth_pwd)
            ftp.retrbinary('RETR %s' % remote_filename, local_filename.write)
        except Exception as e:
            LOG.critical('Failed to connect to the device: exception: %s' %e.message)
            return False
        LOG.info('Successfully copied the file %s' %remote_filename)
        return True


    def dictdiff(self, old_dict, new_dict):

        if old_dict is None:
            return True
        if new_dict is None:
            return True

        for key in old_dict.keys():
            if (not new_dict.has_key(key)):
                return True
            elif (old_dict[key] != new_dict[key]):
                return True
        for key in new_dict.keys():
            if (not old_dict.has_key(key)):
                return True
        return False

    def write_file(self, filename, templatename, dictitems):
        PATH = os.path.dirname(os.path.abspath(__file__))
        TEMPLATE_ENVIRONMENT = Environment(
            autoescape=True,
            loader=FileSystemLoader(os.path.join(PATH, 'templates')),
            trim_blocks=True,
            lstrip_blocks = False)
        try:
            with open(filename, 'w') as f:
                btext = TEMPLATE_ENVIRONMENT.get_template(templatename).render(context = dictitems)
                f.write(btext)
                LOG.info("Successfully written %s" %str(filename))
            return True
        except Exception as e:
            LOG.critical("Failed to write the file %s, exception: %s" %(str(filename),e.message))
            return False

    def write_snabb_conf_file(self, config_dict, instance_id):
        SNABB_CONF_FILE = SNABB_FILENAME + str(instance_id) + '.conf'
        return self.write_file(SNABB_CONF_FILE, SNABB_CONF_TEMPLATE,config_dict)

    def write_snabb_cfg_file(self, cfg_dict, instance_id):
        SNABB_CFG_FILE =  SNABB_FILENAME + str(instance_id) + '.cfg'
        return self.write_file(SNABB_CFG_FILE, SNABB_CFG_TEMPLATE, cfg_dict)

    def parse_snabb_config(self, config_dict):
        if config_dict.get('purge', None) is not None:
            # Call the confAction to kill all the Snabb applications after deleting the cfg/conf/binding files
            self.old_cfg = None
            self.old_conf = None
            self.old_binding_filename = None
            self.instances = {}
            ca = ConfAction()
            ca.deleteAction()
            return

        # At first lets clear the present flag in all the instances
        for keys in self.instances:
            self.instances[keys] = 0

        # Action handler to commit actions for conf/cfg/binding changes
        action_handler = ConfAction()

        # description is same for all the instances in the YANG schema
        cfg_dict = {}
        conf_dict = {}
        print config_dict
        descr = config_dict.get('description', "None")
        print config_dict
        remote_binding_table_filename = config_dict['binding']['br'].get('jnx-aug-softwire:binding-table-file',"None")

        # Fetch this binding file from the device
        if remote_binding_table_filename is not "None":
            # New binding table is provided by the user
            new_binding_file = r'/tmp/snabbvmx.binding.new'
            # touch the new file
            open(new_binding_file, 'w+').close()
            if (self.get_binding_file(remote_binding_table_filename, new_binding_file)):
                # Determine if this binding file is different from existing file
                if self.old_binding_filename is None:
                    self.old_binding_filename = r'/tmp/snabbvmx-xe.binding'
                    os.rename(new_binding_file, self.old_binding_filename)
                    self.binding_changed = True
                    LOG.info("Binding Table has changed")
                elif not filecmp.cmp(self.old_binding_filename, new_binding_file):
                    os.rename(new_binding_file,self.old_binding_filename)
                    #os.remove(new_binding_file)
                    self.old_binding_filename = remote_binding_table_filename
                    self.binding_changed = True
                    LOG.info("Binding Table has changed")
                else:
                    LOG.info("Binding Table has not changed")

                if (self.binding_changed):
                    self.binding_changed = False
                    # Send a sighup to all the snabb instances
                    rc = action_handler.bindAction(self.old_binding_filename)
                    if not rc:
                       LOG.critical("Failed to send SIGHUP to the Snabb instances")
                    else:
                       LOG.info("Successfully sent SIGHUP to the Snabb instances")
            else:
                LOG.critical('Failed to copy remote binding file onto the local disk')
                self.old_binding_filename = None
        else:
            LOG.info("No binding table info found in the config")
            self.old_binding_filename = None

        # Parse the config and cfg changes
        new_instance_list = config_dict['binding']['br']['br-instances']['br-instance']
        for instances in new_instance_list:
            #TODO try except loop has to be implemented
            instance_id = instances.get('id',"None")
            # Verify that the old config contains this instance, if not then we need to delete this instance
            self.instances[instance_id] = 1
            cfg_dict['cnf_file_name'] = SNABB_FILENAME + str(instance_id)+'.conf'

            cfg_dict['ipv4'] = instances.get('jnx-aug-softwire:ipv4_address')
            cfg_dict['ipv4_desc'] = descr
            cfg_dict['ipv4_cache_rate'] = instances.get('jnx-aug-softwire:cache_refresh_interval')

            cfg_dict['ipv6'] = instances.get('ipv6_interface',"None")
            cfg_dict['ipv6_desc'] = descr
            #TODO why we have only one cache_refresh_interval in the augmented file?
            cfg_dict['ipv6_cache_rate'] = instances.get('jnx-aug-softwire:cache_refresh_interval')

            # Parse the conf file attributes
            if self.old_binding_filename is not None:
                conf_dict['binding_table'] =  str(self.old_binding_filename)
            else:
                conf_dict['binding_table'] = None

            #TODO: Do we still have the ipv4 and ipv6 parameters below??
            conf_dict['aftr_ipv4_ip'] = instances.get('address',"None")
            conf_dict['ipv4_mtu'] = instances.get('mtu', "None")
            conf_dict['aftr_ipv6_ip'] = instances.get('address',"None")
            conf_dict['ipv6_mtu'] = instances.get('mtu', "None")


            conf_dict['policy_icmpv4_incoming'] = instances['policy_icmpv4_incoming']
            conf_dict['policy_icmpv4_outgoing'] = instances['policy_icmpv4_outgoing']

            #TODO: Following two missing in augmented file
            conf_dict['icmpv4_rate_limiter_n_packets'] = instances['icmpv4_rate_limiter_n_packets']
            conf_dict['icmpv4_rate_limiter_n_seconds'] = instances['icmpv4_rate_limiter_n_seconds']


            conf_dict['policy_icmpv6_incoming'] = instances['policy_icmpv6_incoming']
            conf_dict['policy_icmpv6_outgoing'] = instances['policy_icmpv6_outgoing']
            conf_dict['icmpv6_rate_limiter_n_packets'] = instances['icmpv6_rate_limiter_n_packets']
            conf_dict['icmpv6_rate_limiter_n_seconds'] = instances['icmpv6_rate_limiter_n_seconds']
            mac_path = SNABB_MAC_PATH+str(instance_id)
            # Read the files
            mac_id = ''
            try:
                with open(mac_path) as f:
                    mac_id = f.read().strip()
            except Exception as e:
                LOG.info('Failed to read the file %s due to exception: %s' %(mac_path, e.message))
                return False

            #TODO these parameters are not defined
            conf_dict['aftr_mac_inet_side'] = mac_id
            conf_dict['aftr_mac_b4_side'] = mac_id

            # Take action based on whether the cfg or conf files have changed or not
            ret_cfg, ret_conf = False, False
            cnt = 0
            cfg_changed = False
            LOG.info('New cfg dict = %s' %str(cfg_dict))
            if self.old_cfg is None:
                ret_cfg = self.write_snabb_cfg_file(cfg_dict, instance_id)
                if not ret_cfg:
                    LOG.critical("Failed to write the cfg file")
                    return
            else:
                for cfg_instance in self.old_cfg:
                    if self.old_cfg['cnf_file_name'] == cfg_dict['cnf_file_name']:
                        # Check if the configuration has changed for this new instance
                        if (self.dictdiff(cfg_instance, cfg_dict)):
                            cfg_changed = True
                            self.old_cfg[cnt] = cfg_dict
                            LOG.info("Cfg dictionary has changed")
                            break
                        else:
                            LOG.info("Cfg dictionary has not changed")
                    cnt += 1
                if (cfg_changed):
                    ret_cfg = self.write_snabb_cfg_file(cfg_dict, instance_id)
                    if not ret_cfg:
                        LOG.critical("Failed to write the cfg file")
                        return
            if self.old_conf is None:
                ret_conf = self.write_snabb_conf_file(conf_dict, instance_id)
                if not ret_conf:
                    LOG.critical("Failed to write the conf file")
                    return
            else:
                cnt = 0
                conf_changed = False
                for conf_instance in self.old_conf:
                    if self.old_conf['binding_table'] == conf_dict['binding_table']:
                        if (self.dictdiff(conf_instance, conf_dict)):
                            conf_changed = True
                            self.old_conf[cnt] = conf_dict
                            LOG.info("Conf dictionary has changed")
                            break
                        else:
                            LOG.info("Conf dictionary has not changed")
                    cnt =+ 1
                if (conf_changed):
                    ret_conf = self.write_snabb_conf_file(conf_dict, instance_id)
                    if not ret_conf:
                        LOG.critical("Failed to write the conf file")
                        return


            if ret_conf or ret_cfg:
                # Assume that the instances list is populated here
                ret = action_handler.cfgAction(instance_id)
                if not ret:
                    LOG.critical("Failed to restart the Snabb instance")

        # Few of the instances might have been deleted, we need to kill those instances
        for keys in self.instances:
            if self.instances[keys] == 0:
                # Kill this instance
                LOG.info("Instance id %d is not present, need to kill it" %int(keys))
                ret = action_handler.cfgAction(keys,False)
                if not ret:
                    LOG.critical("Failed to kill the Snabb instance %d" %int(keys))

        return

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
            self.parse_snabb_config(config_dict)

