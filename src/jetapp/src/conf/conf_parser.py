
import os
from common.mylogging import LOG
from conf_action import ConfAction
from conf.conf_globals import dispQ
from jnpr.junos.utils.scp import SCP

settings_map = {
    'jnx-aug-softwire:ingress_drop_action': 'ingress_drop_monitor',
    'jnx-aug-softwire:ingress_drop_threshold': 'ingress_drop_threshold',
    'jnx-aug-softwire:ingress_drop_interval': 'ingress_drop_interval',
    'jnx-aug-softwire:ingress_drop_wait': 'ingress_drop_wait'
}

ipv6_interface_map = {
    'jnx-aug-softwire:cache_refresh_interval': 'cache_refresh_interval',
    'jnx-aug-softwire:fragmentation': 'fragmentation',
    'jnx-aug-softwire:ipv6_ingress_filter': 'ipv6_ingress_filter',
    'jnx-aug-softwire:ipv6_egress_filter': 'ipv6_egress_filter',
    'jnx-aug-softwire:ipv6_address': 'ipv6_address',
}

ipv4_interface_map = {
    'jnx-aug-softwire:cache_refresh_interval': 'cache_refresh_interval',
    'jnx-aug-softwire:fragmentation': 'fragmentation',
    'jnx-aug-softwire:ipv4_ingress_filter': 'ipv4_ingress_filter',
    'jnx-aug-softwire:ipv4_egress_filter': 'ipv4_egress_filter',
    'jnx-aug-softwire:ipv4_address': 'ipv4_address',
}

internal_interface_map = {
    'jnx-aug-softwire:policy_icmpv6_incoming': 'allow-incoming-icmp',
    'jnx-aug-softwire:policy_icmpv6_outgoing': 'allow-outgoing-icmp',
    'tunnel-path-mru': 'mtu',
}

external_interface_map = {
    'jnx-aug-softwire:policy_icmpv4_incoming': 'allow-incoming-icmp',
    'jnx-aug-softwire:policy_icmpv4_outgoing': 'allow-outgoing-icmp',
    'tunnel-payload-mtu': 'mtu',
}

instance_external_interface_map = {
    'jnx-aug-softwire:ipv4_address': 'ip',
    'jnx-aug-softwire:ipv4_vlan': 'vlan-tag',

}

instance_internal_interface_map = {
    'jnx-aug-softwire:ipv6_address': 'ip',
    'jnx-aug-softwire:ipv6_vlan': 'vlan-tag',
}

class ParseNotification:
    def __init__(self, device):
        self.binding_changed = False
        self.old_cfg = None
        self.old_conf = None
        self.old_binding_filename = None
        self._dev = device
        # All the instances will be added to this list
        self.instances = {}

    def get_binding_file(self, remote_filename, local_path):
        try:
            # Create a Pyez connection with the device
            with SCP(self._dev.dev) as scp:
                scp.get(remote_filename, local_path)
        except Exception as e:
            LOG.critical('Failed to connect to the device: exception: %s' %e.message)
            return False
        LOG.info('Successfully copied the file %s' %remote_filename)
        return True



    def map_newkey(self, smap, key, value, indent, snabbvmx):
        newkey = smap.get(key, None)
        if newkey:
            if value == 'allow':
                value = 'true'

            elif value == 'deny':
                value = 'false'

            elif value == 'false':
                value = 'false'

            elif value == 'true':
                value = 'true'

            elif snabbvmx:
                try:
                    val = int(value)
                except ValueError:
                    value = '"%s"' % (value)

            if snabbvmx:
                return "%s%s = %s;\n" % (' ' * indent, newkey, value)
            else:
                return "%s%s %s;\n" % (' ' * indent, newkey, value)

        else:
            return ""


    def binding_table_from_dict(self, bt):
        t = ''

        entries = bt.get('binding-entry', [])
        for entry in entries:
            ipv4 = entry.get('binding-ipv4-addr', '0.0.0.0')
            b4_ipv6 = entry.get('binding-ipv6info', '')
            br_address = entry.get('br-ipv6-addr', '')
            port_set = entry.get('port-set', {})
            psid = port_set.get('psid', '0')
            offset = port_set.get('psid-offset', '0')
            psid_len = port_set.get('psid-len', '0')
            t = t + "    softwire { ipv4 %s; psid %s; b4-ipv6 %s; br-address %s; " % (
                ipv4, psid, b4_ipv6, br_address)
            t = t + " port-set { psid-length %s; }}\n" % (psid_len)
        return t


    def binding_table_from_file(self, binding_table_file):
        t = ''
        br_address = ''
        remote_file="/var/db/scripts/commit/" + binding_table_file
        new_binding_table_file = r'/tmp/' + binding_table_file
        if (self.get_binding_file(remote_file, r'/tmp/')):
            LOG.info("Binding Table file %s transferred" %binding_table_file)
        else:
            LOG.critical("Failed to transfer binding table file %s" %binding_table_file)
            return ''

        with open(new_binding_table_file) as f:
            for line in f:
                line = line.rstrip('\n')
                b4_ipv6, value = line.split(" ")
                if b4_ipv6 == 'apply-macro':
                    sw, br_address = value.split("_")
                else:
                    ipv4, psid, psid_len, offset = value.split(",")
                    t = t + "    softwire { ipv4 %s; psid %s; b4-ipv6 %s; br-address %s; " % (
                        ipv4, psid, b4_ipv6, br_address)
                    t = t + " port-set { psid-length %s; }}\n" % (psid_len)

            f.close

        return t


    def lwaftr_config(self, instance, default_binding_table):
        instance_id = instance.get('id', None)
        LOG.info("lwaftr_config instance_id=%d" %instance_id)
        if instance_id == None:
            return

        snabbvmx_conf = "return {\n  lwaftr = \"lwaftr-xe%s.conf\",\n" % (instance_id)
        lwaftr_conf = "softwire-config {\n"

        mac_path = 'mac_xe'+str(instance_id)
        mymac = ''
        try:
            with open(mac_path) as f:
                mymac = f.read().strip()
        except Exception as e:
            LOG.info('Failed to read the file %s due to exception: %s' %(mac_path, e.message))
            return False

        binding_table_file = instance.get(
            'jnx-aug-softwire:binding-table-file', default_binding_table)

        settings = ''
        ipv4_interface = ''
        ipv6_interface = ''
        internal_interface = ''
        external_interface = ''
        instance_internal_interface = ''
        instance_external_interface = ''

        for key, value in instance.items():
            #        print "%s:%s" % (' '*indent, key, value)
            settings = settings + self.map_newkey(settings_map, key, value, 4, True)
            ipv6_interface = ipv6_interface + \
                self.map_newkey(ipv6_interface_map, key, value, 4, True)
            ipv4_interface = ipv4_interface + \
                self.map_newkey(ipv4_interface_map, key, value, 4, True)

            internal_interface = internal_interface + \
                self.map_newkey(internal_interface_map, key, value, 4, False)
            external_interface = external_interface + \
                self.map_newkey(external_interface_map, key, value, 4, False)

            instance_internal_interface = instance_internal_interface + \
                self.map_newkey(instance_internal_interface_map, key, value, 8, False)
            instance_external_interface = instance_external_interface + \
                self.map_newkey(instance_external_interface_map, key, value, 8, False)

        if settings:
            settings = "  settings = {\n" + settings + "  },\n"

        instance_external_interface = instance_external_interface + \
            "        mac %s;\n        next-hop {\n" % (mymac)
        instance_external_interface = instance_external_interface + \
            "          mac 02:02:02:02:02:02;\n       }\n"

        instance_internal_interface = instance_internal_interface + \
            "        mac %s;\n        next-hop {\n" % (mymac)
        instance_internal_interface = instance_internal_interface + \
            "          mac 02:02:02:02:02:02;\n       }\n"

        snabbvmx_conf = snabbvmx_conf + settings
        snabbvmx_conf = snabbvmx_conf + \
            "  ipv6_interface = {\n" + ipv6_interface + "  },\n"
        snabbvmx_conf = snabbvmx_conf + \
            "  ipv4_interface = {\n" + ipv4_interface + "  },\n" + "}\n"

        lwaftr_conf = lwaftr_conf + \
            "  external-interface {\n" + external_interface + "  }\n"
        lwaftr_conf = lwaftr_conf + "  instance {\n    device xe%d;\n" % (instance_id)
        lwaftr_conf = lwaftr_conf + "    queue {\n      id %d;\n" % (instance_id)
        lwaftr_conf = lwaftr_conf + \
            "      external-interface {\n" + \
            instance_external_interface + "      }\n"
        lwaftr_conf = lwaftr_conf + \
            "      internal-interface {\n" + \
            instance_internal_interface + "      }\n"
        lwaftr_conf = lwaftr_conf + "    }\n  }\n"
        lwaftr_conf = lwaftr_conf + \
            "  internal-interface {\n" + internal_interface + "  }\n"

        bt = instance.get('binding-table', None)
        if bt:
            binding_table = self.binding_table_from_dict(bt)
        else:
            binding_table = self.binding_table_from_file(binding_table_file)

        lwaftr_conf = lwaftr_conf + "  binding-table {\n" + binding_table + "  }\n"

        lwaftr_conf = lwaftr_conf + "}\n"

        snabbvmx_conf_filename = 'xe%d.conf' % (instance_id)
        lwaftr_conf_filename = 'lwaftr-' + snabbvmx_conf_filename

        changed = True

        try:
            f = open(snabbvmx_conf_filename, 'r')
        except:
            print("can't read file " + snabbvmx_conf_filename)
        else:
            previous = f.read()
            if previous == snabbvmx_conf:
                changed = False
            f.close

            if changed == False:
                try:
                    f = open(lwaftr_conf_filename, 'r')
                except:
                    changed = True
                    print("can't read file " + lwaftr_conf_filename)
                else:
                    previous = f.read()
                    if previous == lwaftr_conf:
                        changed = False
                    else:
                        changed = True
                    f.close()

        if changed == True:
            LOG.info("config Changed %s %s!!" % (snabbvmx_conf_filename, lwaftr_conf_filename))
            with open(snabbvmx_conf_filename, 'w') as f:
                f.write(snabbvmx_conf)
                f.close()

            with open(lwaftr_conf_filename, 'w') as f:
                f.write(lwaftr_conf)
                f.close()

        return changed


    def parse_snabb_config(self, config_dict):

        # Action handler to commit actions for conf/cfg/binding changes
        action_handler = ConfAction()

        try:
            br = config_dict['binding']['br']
        except:
            LOG.info("no br-instances found")
            action_handler.deleteAction()
            return

        default_binding_table = br.get("jnx-aug-softwire:binding-table-file", '')
        LOG.info("default binding table: %s" % (default_binding_table))

        try:
            instances = br['br-instances']['br-instance']
        except:
            LOG.info("no br-instance found")
            exit(0)

        if isinstance(instances, list):
            for instance in instances:
                if isinstance(instance, dict):
                    changed = self.lwaftr_config(instance, default_binding_table)
                    instance_id = instance.get('id', None)
                    if changed:
                        LOG.info("restarting instance %d" %instance_id)
                        ret = action_handler.cfgAction(instance_id)

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
