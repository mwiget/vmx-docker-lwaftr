#!/usr/bin/python
import json

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

ipv6_address = ''

def map_newkey(smap, key, value, indent, snabbvmx):
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


def binding_table_from_dict(bt):
    t = ''
    global ipv6_address

    entries = bt.get('binding-entry', [])
    for entry in entries:
        ipv4 = entry.get('binding-ipv4-addr', '0.0.0.0')
        b4_ipv6 = entry.get('binding-ipv6info', '')
        br_address = entry.get('br-ipv6-addr', '')
        ipv6_address = br_address
        port_set = entry.get('port-set', {})
        psid = port_set.get('psid', '0')
        offset = port_set.get('psid-offset', '0')
        psid_len = port_set.get('psid-len', '0')
        t = t + "    softwire { ipv4 %s; psid %s; b4-ipv6 %s; br-address %s; " % (
            ipv4, psid, b4_ipv6, br_address)
        t = t + " port-set { psid-length %s; }}\n" % (psid_len)
    return t


def binding_table_from_file(binding_table_file):
    t = ''
    global ipv6_address
    br_address = ''
    with open(binding_table_file) as f:
        for line in f:
            line = line.rstrip('\n')
            b4_ipv6, value = line.split(" ")
            if b4_ipv6 == 'apply-macro':
                sw, br_address = value.split("_")
                ipv6_address = br_address
            else:
                ipv4, psid, psid_len, offset = value.split(",")
                t = t + "    softwire { ipv4 %s; psid %s; b4-ipv6 %s; br-address %s; " % (
                    ipv4, psid, b4_ipv6, br_address)
                t = t + " port-set { psid-length %s; }}\n" % (psid_len)

        f.close

    return t


def lwaftr_config(instance, default_binding_table):
    print "calling lwaftr_config"
    id = instance.get('id', None)
    if id == None:
        return

    snabbvmx_conf = "return {\n  lwaftr = \"lwaftr-xe%s.conf\",\n" % (id)
    lwaftr_conf = "softwire-config {\n"

    with open('mac_xe%d' % (id), 'r') as myfile:
        mymac = myfile.read()
        mymac = mymac.rstrip('\n')
        myfile.close

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
        settings = settings + map_newkey(settings_map, key, value, 4, True)
        ipv6_interface = ipv6_interface + \
            map_newkey(ipv6_interface_map, key, value, 4, True)
        ipv4_interface = ipv4_interface + \
            map_newkey(ipv4_interface_map, key, value, 4, True)

        internal_interface = internal_interface + \
            map_newkey(internal_interface_map, key, value, 4, False)
        external_interface = external_interface + \
            map_newkey(external_interface_map, key, value, 4, False)

        instance_internal_interface = instance_internal_interface + \
            map_newkey(instance_internal_interface_map, key, value, 8, False)
        instance_external_interface = instance_external_interface + \
            map_newkey(instance_external_interface_map, key, value, 8, False)

    if settings:
        settings = "  settings = {\n" + settings + "  },\n"

    instance_external_interface = instance_external_interface + \
        "        mac %s;\n        next-hop {\n" % (mymac)
    instance_external_interface = instance_external_interface + \
        "          mac 02:02:02:02:02:02;\n       }\n"

    instance_internal_interface = instance_internal_interface + \
        "        ip %s;\n" % (ipv6_address)
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
    lwaftr_conf = lwaftr_conf + "  instance {\n    device xe%d;\n" % (id)
    lwaftr_conf = lwaftr_conf + "    queue {\n      id %d;\n" % (id)
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
        binding_table = binding_table_from_dict(bt)
    else:
        binding_table = binding_table_from_file(binding_table_file)

    print "ipv6_address=%s"% ipv6_address

    lwaftr_conf = lwaftr_conf + "  binding-table {\n" + binding_table + "  }\n"

    lwaftr_conf = lwaftr_conf + "}\n"

    snabbvmx_conf_filename = 'xe%d.conf' % (id)
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
                    print "setting changed to False"
                    changed = False
                else:
                    changed = True
                f.close()

    print ("after check")

    if changed == True:
        print "config Changed %s %s!!" % (snabbvmx_conf_filename, lwaftr_conf_filename)
        with open(snabbvmx_conf_filename, 'w') as f:
            f.write(snabbvmx_conf)
            f.close()

        with open(lwaftr_conf_filename, 'w') as f:
            f.write(lwaftr_conf)
            f.close()

#        print "xe%d.conf:" % (id)
#        print snabbvmx_conf
#        print ""
#        print "lwaftr-xe%d.conf:" % (id)
#        print lwaftr_conf
#        print ""


with open("lwaftr.json", "r") as f:
    d = json.load(f)
    try:
        br = d['ietf-softwire:softwire-config']['binding']['br']
    except:
        print "no br-instances found"
        exit(0)

    default_binding_table = br.get("jnx-aug-softwire:binding-table-file", '')
    print "default binding table: %s" % (default_binding_table)

    try:
        instances = br['br-instances']['br-instance']
    except:
        print "no instances found"
        exit(0)

    if isinstance(instances, list):
        for instance in instances:
            if isinstance(instance, dict):
                lwaftr_config(instance, default_binding_table)
