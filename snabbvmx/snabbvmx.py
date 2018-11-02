#!/usr/bin/env python3
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

from __future__ import print_function

# import os.path
import os
import sys
import argparse
import logging
import socket
import netaddr
import paho.mqtt.client as mqtt
from jnpr.junos import Device
from jnpr.junos.op.ethport import EthPortTable
from lxml import etree
#import jxmlease
from subprocess import Popen, PIPE

import grpc
import authentication_service_pb2
import bgp_route_service_pb2
import prpd_common_pb2
import jnx_addr_pb2

_JET_TIMEOUT = 10  # Timeout in seconds for an rpc to return back
SNABB = "/bin/snabb"

ipv4mask = '/29'
ipv6mask = '/64'

# Route parameters
local_pref = 100
route_pref = 10

class DictDiffer(object):

    """
    Source: https://github.com/hughdbrown/dictdiffer

    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """

    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(
            current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])


def get_snabb_config(id):

    # dump lwaftr binding table and instance
    with Popen([SNABB, "config", "get", "-s", "snabb-softwire-v2", id, "/"], stdout=PIPE, stderr=PIPE) as p:
        out, err = p.communicate()
        data = out.decode('ascii')

    if data:
        logging.debug("snabb: %s" % out)
    if err:  # not really errors in case of snabb.
        logging.error("snabb: %s" % err)
    if p.returncode == 0:
        logging.info("snabb: running configuration successfully retrieved")
    else:
        logging.error("snabb: returned error {0}".format(p.returncode))

    return data

def flushRoutes(bgp):
    strBgpReq = bgp_route_service_pb2.BgpRouteCleanupRequest()
    result = bgp.BgpRouteCleanup(strBgpReq, timeout=_JET_TIMEOUT)
    print('BgpRouteCleanup API return = %d' % result.status)
    if result.status != bgp_route_service_pb2.BgpRouteCleanupReply.SUCCESS:
        print('Error on Cleanup')

def routePrefix(route):

    global ipv4plen
    global ipv6plen

    ip = netaddr.IPAddress(route)
    if ip.version == 6:
        tbl = 'inet6.0'
        destPrefix = prpd_common_pb2.RoutePrefix(
            inet6=jnx_addr_pb2.IpAddress(addr_string=route))
        ipn = netaddr.IPNetwork(route + ipv6mask)
        if ipn.network == ipn.ip:
            prefix_len = ipv6plen
        else:
            prefix_len = 128
    else:
        tbl = 'inet.0'
        destPrefix = prpd_common_pb2.RoutePrefix(
            inet=jnx_addr_pb2.IpAddress(addr_string=route))
        ipn = netaddr.IPNetwork(route + ipv4mask)
        if ipn.network == ipn.ip:
            prefix_len = ipv4plen
        else:
            prefix_len = 32
    return tbl, destPrefix, prefix_len

def routeMatch(nh, tbl, destPrefix, prefix_len):

    nextHopIp = jnx_addr_pb2.IpAddress(addr_string=nh)
    rt_table = prpd_common_pb2.RouteTable(
        rtt_name=prpd_common_pb2.RouteTableName(name=tbl))
    routeParams = bgp_route_service_pb2.BgpRouteMatch(
        dest_prefix=destPrefix, dest_prefix_len=prefix_len,
        table=rt_table)
    return routeParams

def routeEntry(nh, tbl, destPrefix, prefix_len):

    path_cookie = int(netaddr.IPAddress(nh)) & 0xffffffff
    nextHopIp = jnx_addr_pb2.IpAddress(addr_string=nh)
    rt_table = prpd_common_pb2.RouteTable(
        rtt_name=prpd_common_pb2.RouteTableName(name=tbl))
    routeParams = bgp_route_service_pb2.BgpRouteEntry(
        dest_prefix=destPrefix, dest_prefix_len=prefix_len,
        table=rt_table,
        protocol_nexthops=[nextHopIp],
        path_cookie=path_cookie,
        route_type=bgp_route_service_pb2.BGP_INTERNAL,
        local_preference=bgp_route_service_pb2.BgpAttrib32(
            value=local_pref),
        route_preference=bgp_route_service_pb2.BgpAttrib32(
            value=route_pref),
        protocol=bgp_route_service_pb2.PROTO_BGP_STATIC)
#        aspath=bgp_route_service_pb2.AsPath(aspath_string=asPathStr))
    return routeParams


def extract_aggregates(data):

    global ipv4mask
    global ipv6mask

    routes = {}
    nexthops = {}

    skipline = False

    for line in data.split('\n'):
#    for line in data.split('\\n'):
        line = line.lstrip()
        line = line.rstrip(';')
        kv = line.split(' ')

        if skipline == True:
            skipline = False
            continue

        if 'next-hop' in line:
            skipline = True
            continue

        if len(kv) == 2:
            key = kv[0]
            value = kv[1]

            if key == 'b4-ipv6':
                ip = netaddr.IPNetwork(value + ipv6mask)
                ip_net = str(ip.network)
                routes[ip_net] = routes.get(ip_net, 0) + 1
            elif key == 'ipv4':
                ip = netaddr.IPNetwork(value + ipv4mask)
                ip_net = str(ip.network)
                routes[ip_net] = routes.get(ip_net, 0) + 1
            elif key == 'br-address':
                routes[value] = routes.get(value, 0) + 1
            elif key == 'ip':
                nexthops[value] = nexthops.get(value, 0) + 1

    return routes, nexthops
def read_binding_table(filename, out):
    count = 0
    try:
        with open(filename) as f:
            line = f.readline().rstrip()
            braddress = line.split("_")
            for line in f:
                elements = re.split(" |,", line)
                print("    softwire {", file=out)
                print("      b4-ipv6 %s;" % elements[0], file=out)
                print("      ipv4 %s;" % elements[1], file=out)
                print("      psid %s;" % elements[2], file=out)
                print("      br-address %s;" % braddress[1], file=out)
                print("      port-set {\n        psid-length %s;" % elements[3], file=out)
                print("      }", file=out)
                print("    }", file=out)
                count = count + 1
    except Exception as e:
        logging.error(
            "Failed to read binding table from file %s exception: %s" % (filename, e.message))
        return
    logging.info("imported %d bindings from from %s" % (count, filename))
    return


def query_config(userdata):
    logging.info("grab softwire config from " +
                 userdata.target + " as user " + userdata.username)
    logging.info("ssh private_key file " + userdata.private_key)
    logging.basicConfig(level=logging.WARNING)
    try:
        pyez_client = Device(host=userdata.target, user=userdata.username,
                             ssh_private_key_file=userdata.private_key, gather_facts=False)
        pyez_client.open()
    except Exception as e:
        logging.error(
            "Failed to connect to the device, error: {0}".format(e))
        return
    result = pyez_client.rpc.get_config(
        filter_xml="softwire-config", model="custom", namespace="snabb:softwire-v2", normalize=True)

    ether = {}   # fill table indexed by snabb interface name containing mac address used by vMX
    iftable = EthPortTable(pyez_client)
    iftable.get()
    logging.basicConfig(level=logging.INFO)
    for ifentry in iftable:
        if ifentry.description:
            elements = ifentry.description.split('@')
            if 2 == len(elements) and "xe" in elements[0]:
                logging.debug("interface %s (%s) has macaddr %s" %
                              (ifentry.name, elements[1], ifentry.macaddr))
                ether[elements[1]] = ifentry.macaddr

    pyez_client.close()
    out = open(userdata.outputfile, "w")

    # set current mac address to passthru-interfaces
    for item in result.iterfind(".//passthru-interface"):
        name = item.find("device").text
        item.find("mac").text = ether[name]

    def walkchild(element, level, out):
        closing = False
        indent = level * 2
        if element.text:
            print(" " * indent + element.tag + " " + element.text + ";", file=out)
        else:
            print(" " * indent + element.tag + " {", file=out)
            closing = True
        if len(element):
            for child in element.getchildren():
                walkchild(child, level+1, out)
            if closing:
                print(" " * indent + "}", file=out)

    print("softwire-config {", file=out)

    for item in result.iterfind("./instance"):
        walkchild(item, 1, out)

    for item in result.iterfind("./external-interface"):
        walkchild(item, 1, out)

    for item in result.iterfind("./internal-interface"):
        walkchild(item, 1, out)

    print("  binding-table {", file=out)

    binding_table_file = result.findtext("binding-table-file")
    if binding_table_file:
        logging.debug("binding file " + binding_table_file)
        read_binding_table(binding_table_file, out)

    for item in result.iterfind(".//softwire"):
        walkchild(item, 2, out)

    print("  }", file=out)
    print("}", file=out)

    out.close()
    with Popen([SNABB, "config", "load", "-s", "snabb-softwire-v2", userdata.snabbid, userdata.outputfile], stdout=PIPE, stderr=PIPE) as p:
        out, err = p.communicate()
        if out:
            logging.info("snabb: %s" % out)
        if err:  # not really errors in case of snabb.
            logging.info("snabb: %s" % err)
        if p.returncode == 0:
            logging.info("snabb: successfully loaded configuration")
        else:
            logging.error("snabb: returned error {0}".format(p.returncode))
    return


def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code {0}".format(str(rc)))
    client.subscribe("/junos/events/syslog/UI_COMMIT_COMPLETED")
    logging.info("subscribed to UI_COMMIT_COMPLETED")


def on_message(client, userdata, msg):
    logging.debug("Message received-> " + msg.topic + " " + str(msg.payload))
    query_config(userdata)


def grpc_authenticate(channel, args):

    logging.debug("Trying to Login to", args.target, "port",
                  args.grpc_port, "as user", args.username, "... ")
    if args.password == 'none' and args.target:
        filename = '.' + args.target + '.pwd'
        with open(filename, 'r') as mypwd:
            password = mypwd.read().replace('\n', '')
        mypwd.close()
        logging.debug("root password read from file " + filename)
    else:
        password = args.password

    auth_stub = authentication_service_pb2.LoginStub(channel)
    login_response = auth_stub.LoginCheck(
        authentication_service_pb2.LoginRequest(
            user_name=args.username,
            password=password,
            client_id=socket.gethostname()), _JET_TIMEOUT)

    if login_response.result == 1:
        logging.info("gRPC Login successful")
    else:
        logging.error("gRPC Login failed")
        sys.exit(1)


def main():

    global ipv4plen
    global ipv6plen

    parser = argparse.ArgumentParser(description="snabbvmx")
    parser.add_argument("-t", "--target", dest="target", default="vmx1")
    parser.add_argument("-m", "--mqtt_port", type=int,
                        dest="mqtt_port", default=1883)
    parser.add_argument("-g", "--grpc_port", type=int,
                        dest="grpc_port", default=50051)
    parser.add_argument("-u", "--user", dest="username", default="root")
    parser.add_argument("-p", "--password", dest="password",
                        help="password for grpc access", default="none")
    parser.add_argument("-P", "--private_key",
                        dest="private_key", help="ssh private keyfile for netconf access", default="id_rsa")
    parser.add_argument("-o", "--outputfile",
                        dest="outputfile", default="/tmp/snabb.conf")
    parser.add_argument("-d", "--debug", help="debug level",
                        dest="debug", action="store_true")
    parser.add_argument('-i', '--id', dest='snabbid', default='lwaftr')
    parser.add_argument("-s", "--single", help="single query",
                        dest="single", action="store_true")
    parser.add_argument('-4', '--ipv4plen',
                        dest='ipv4plen', type=int, default=29)
    parser.add_argument('-6', '--ipv6plen',
                        dest='ipv6plen', type=int, default=64)
    args = parser.parse_args()

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.propagate = False
    if args.debug:
        root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    root.handlers = [ch]

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("debug logging enabled")
    else:
        logging.basicConfig(level=logging.INFO)

    if args.single:
        query_config(userdata=args)
    else:
        logging.info("connecting to " + args.target +
                     " mqtt port " + str(args.mqtt_port) + " ...")
        client = mqtt.Client(client_id=os.path.basename(
            __file__)+str(os.getpid()), userdata=args)

        logging.info("connecting to " + args.target +
                     " gRPC port " + str(args.grpc_port) + " ...")
        channel = grpc.insecure_channel(
            '%s:%d' % (args.target, args.grpc_port))
        grpc_authenticate(channel, args)

        # Create the BGP service stub
        bgp = bgp_route_service_pb2.BgpRouteStub(channel)
        strBgpReq = bgp_route_service_pb2.BgpRouteInitializeRequest()
        result = bgp.BgpRouteInitialize(strBgpReq, timeout=_JET_TIMEOUT)
        if ((result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS) and
             (result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS_STATE_REBOUND)):
                 logging.error('Error on BgpRouteInitializeRequest')
        logging.info("Successfully connected to BGP Route Service on %s" % args.target)

        old_routes = {}
        old_nexthops = {}

        ipv4plen = args.ipv4plen
        ipv4mask = '/' + str(ipv4plen)
        ipv6plen = args.ipv6plen
        ipv6mask = '/' + str(ipv6plen)

        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(args.target, args.mqtt_port, 60)
        while True:
            client.loop(timeout=10.0)

            # now grab config from snabb 

            data = get_snabb_config(args.snabbid)
            if data == False:
                print('snabb socket closed. Purge all routes!')
                flushRoutes(bgp)
                sys.exit(1)

            new_routes, new_nexthops = extract_aggregates(data)

            logging.debug("new_routes: %s" % new_routes)
            reachable_nexthops_keys = sorted(new_nexthops.keys())
            reachable_v6_nh = [s for s in reachable_nexthops_keys if ":" in s]
            reachable_v4_nh = [s for s in reachable_nexthops_keys if "." in s]
            logging.info("received %d routes with %d (out of %d) reachable next hops" %
                  (len(new_routes), len(new_nexthops), len(new_nexthops)))
            logging.debug("reachable_v4_nh %s" % reachable_v4_nh)
            logging.debug("reachable_v6_nh %s" % reachable_v6_nh)

            for route in new_routes:
                if ':' in route:
                    new_routes[route] = reachable_v6_nh
                else:
                    new_routes[route] = reachable_v4_nh

            logging.debug("new_routes: %s" % new_routes)

            changed_routes = DictDiffer(new_routes, old_routes)

            rtremlist = []

            for route in changed_routes.removed():
                logging.debug("REMOVE ROUTE %s" % route)
                tbl, destPrefix, prefix_len = routePrefix(route)
                rtlremist.append(routeMatch(nh, tbl, destPrefix, prefix_len))

            rtlist = []

            for route in changed_routes.changed():
                tbl, destPrefix, prefix_len = routePrefix(route)
                logging.debug("CHANGE ROUTE %s:%s" % (route, new_routes[route]))
                # remove the route using cookie 0, to remove all paths
                rtremlist.append(routeMatch(nh, tbl, destPrefix, prefix_len))
                # Build the route table objects for each next hop
                # once the BGP JET API supports multiple next hops per route, this can be
                # replaced with a single rpc call
                for nh in new_routes[route]:
                    rtlist.append(
                        routeEntry(nh, tbl, destPrefix, prefix_len))

            for route in changed_routes.added():
                tbl, destPrefix, prefix_len = routePrefix(route)
                logging.debug("ADD ROUTE %s nh %s prefix_len=%d" % (route,new_routes[route], prefix_len))
                # Build the route table objects for each next hop
                # once the BGP JET API supports multiple next hops per route, this can be
                # replaced with a single rpc call
                for nh in new_routes[route]:
                    rtlist.append(
                        routeEntry(nh, tbl, destPrefix, prefix_len))

            if len(rtremlist) > 0:
                routeUpdReq = bgp_route_service_pb2.BgpRouteRemoveRequest(
                    bgp_routes=rtremlist)
                result = bgp.BgpRouteRemove(routeUpdReq, _JET_TIMEOUT)
                if result.status > bgp_route_service_pb2.BgpRouteOperReply.SUCCESS:
                    logging.error("BgpRouteRemove failed with code", result.status)
                else:
                    logging.info("BgpRouteRemove routes successfully removed")

            if len(rtlist) > 0:
                routeUpdReq = bgp_route_service_pb2.BgpRouteUpdateRequest(
                    bgp_routes=rtlist)
                result = bgp.BgpRouteUpdate(routeUpdReq, _JET_TIMEOUT)
                if result.status > bgp_route_service_pb2.BgpRouteOperReply.SUCCESS:
                    logging.error("BgpRouteAdd failed with code", result.status)
                else:
                    logging.info("BgpRouteAdd routes successfully updated")

            old_routes = new_routes
            data = ''

            logging.debug("--- idle ---")


if __name__ == "__main__":
    main()




