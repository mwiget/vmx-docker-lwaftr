#!/usr/bin/env python
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

from __future__ import print_function

import socket
import time
import sys
import netaddr
import grpc
import argparse
import os, os.path

import authentication_service_pb2
import bgp_route_service_pb2
import prpd_common_pb2
import jnx_addr_pb2

DEFAULT_APP_COOKIE = 12345678

_JET_TIMEOUT = 10  # Timeout in seconds for an rpc to return back

noauth = True

debug = False

ipv4mask = 24
ipv6mask = 64

# Route parameters
local_pref = 100
route_pref = 10
commListStr = None
asPathStr = None
originator = '10.255.255.3'
cluster = '10.255.255.7'


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


# Build a Network Address object given an address string and family
def net_addr(addrStr, family):
    if family is 'inet':
        return NetworkAddress(inet=jnx_addr_pb2.IpAddress(addr_string=addrStr))
    elif family is 'inet6':
        return NetworkAddress(inet6=jnx_addr_pb2.IpAddress(addr_string=addrStr))
    else:
        return False


def extract_aggregates(data):

    global ipv4mask
    global ipv6mask

    routes = {}
    nexthops = {}

    skipline = False

    for line in data.split('\\n'):
        #        print line
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


def grpc_authenticate(channel, args):

    try:
        # port 40041 only works when local to rpd and bypasses authentication
        if args.port == 40041:
            print("bypassing authentication")

        else:
            print("Trying to Login to", args.grpc, "port",
                  args.port, "as user", args.username, "... ", end='')
            if args.password == 'none' and args.grpc:
                filename='/u/.' + args.grpc + '.pwd'
                with open(filename, 'rb') as mypwd:
                    password = mypwd.read().replace('\n', '')
                mypwd.close()
                print("root password read from file " + filename)
            else:
                password=args.password

            auth_stub = authentication_service_pb2.LoginStub(channel)
            login_response = auth_stub.LoginCheck(
                authentication_service_pb2.LoginRequest(
                    user_name=args.username,
                        password=password,
                        client_id=socket.gethostname()), _JET_TIMEOUT)

            if login_response.result == 1:
                print("Junos Login successful")
            else:
                print("Junos Login failed")
                sys.exit(1)

    except Exception as tx:
        print(tx)


def flushRoutes(bgp):
    strBgpReq = bgp_route_service_pb2.BgpRouteCleanupRequest()
    result = bgp.BgpRouteCleanup(strBgpReq, timeout=_JET_TIMEOUT)
    print('BgpRouteCleanup API return = %d' % result.status)
    if result.status != bgp_route_service_pb2.BgpRouteCleanupReply.SUCCESS:
        print('Error on Cleanup')


def get_snabb_config(sock):

    # dump lwaftr binding table and instance
    message = '{ "id": "0", "verb": "get", "schema": "snabb-softwire-v2", "path": "/" }'
    if debug:
        print("requesting", message)
    try:
        sock.sendall(message)

        data = ''
        while True:
            data = data + sock.recv(8192)
            if data:
                if '"id":"0"}' in data:
                    break
            else:
                break

    except:
        return False

    return data


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
        protocol=bgp_route_service_pb2.PROTO_BGP_STATIC,
        aspath=bgp_route_service_pb2.AsPath(aspath_string=asPathStr))
    if originator != 'none':
        routeParams.originator_id.value = socket.htonl(
            int(netaddr.IPAddress(originator)))
    if cluster != 'none':
        routeParams.cluster_id.value = socket.htonl(
            int(netaddr.IPAddress(cluster)))
    if commListStr:
        for comm in commListStr.split():
            routeParams.communities.com_list.add(
            ).community_string = comm
    return routeParams


def main():
    global ipv4mask
    global ipv6mask
    global ipv4plen
    global ipv6plen
    global cookie
    global debug

    tbl = ''

    global _JET_TIMEOUT

    parser = argparse.ArgumentParser()
    parser.add_argument('snabb', help='hostname running lwaftr instance')
    parser.add_argument('-s', '--socket', dest='socket', default='4321',
                        help='unix socket or TCP port')
    parser.add_argument(
        '-4', '--ipv4plen', dest='ipv4plen', type=int, default=24)
    parser.add_argument(
        '-6', '--ipv6plen', dest='ipv6plen', type=int, default=64)
    parser.add_argument('-g', '--grpc', dest='grpc', default='crr')
    parser.add_argument('-P', '--port', dest='port', type=int, default=40041)
    parser.add_argument('-u', '--user', dest='username', default='none')
    parser.add_argument('-p', '--pass', dest='password', default='none')
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()
    debug = args.debug

    ipv4plen = args.ipv4plen
    ipv4mask = '/' + str(ipv4plen)
    ipv6plen = args.ipv6plen
    ipv6mask = '/' + str(ipv6plen)

    if (args.socket.isdigit()):
        print('Connect to', args.snabb, 'via TCP socket: ', args.socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (args.snabb, int(args.socket))
    else:
        if os.path.exists(args.socket):
            print('Connect to snabb via unix socket: ', args.socket)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server_address = args.socket
        else:
            print('socket not found: ', args.socket)
            sys.exit(1)

    print('Connect to Junos via gRPC: ', args.grpc, ':', args.port)
    print('Aggregate IPv4 routes to', ipv4mask)
    print('Aggregate IPv6 routes to', ipv6mask)

    print("server: ", server_address)
    try:
        sock.connect(server_address)
    except socket.error, msg:
        print (msg, file=sys.stderr)
        print('abort')
        sys.exit(1)

    channel = grpc.insecure_channel('%s:%d' % (args.grpc, args.port))
    grpc_authenticate(channel, args)

    # Create the BGP service stub
    bgp = bgp_route_service_pb2.BgpRouteStub(channel)
    strBgpReq = bgp_route_service_pb2.BgpRouteInitializeRequest()
    result = bgp.BgpRouteInitialize(strBgpReq, timeout=_JET_TIMEOUT)
    if ((result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS) and
            (result.status != bgp_route_service_pb2.BgpRouteInitializeReply.SUCCESS_STATE_REBOUND)):
        print('Error on Initialize')
    print("Successfully connected to BGP Route Service")

    old_routes = {}
    old_nexthops = {}

    while True:

        data = get_snabb_config(sock)
        if data == False:
            print('snabb socket closed. Purge all routes!')
            flushRoutes(bgp)
            sys.exit(1)

        new_routes, new_nexthops = extract_aggregates(data)

        if debug:
            print("new_routes: ", new_routes)
        reachable_nexthops_keys = sorted(new_nexthops.keys())
        reachable_v6_nh = [s for s in reachable_nexthops_keys if ":" in s]
        reachable_v4_nh = [s for s in reachable_nexthops_keys if "." in s]
        print("received %d routes with %d (out of %d) reachable next hops" %
              (len(new_routes), len(new_nexthops), len(new_nexthops)))
        if debug:
            print("reachable_v4_nh", reachable_v4_nh)
            print("reachable_v6_nh", reachable_v6_nh)

        for route in new_routes:
            if ':' in route:
                new_routes[route] = reachable_v6_nh
            else:
                new_routes[route] = reachable_v4_nh

        if debug:
            # each route contains now family specific next hops
            print("new_routes: ", new_routes)

        changed_routes = DictDiffer(new_routes, old_routes)

        rtremlist = []

        for route in changed_routes.removed():
            if debug:
                print("REMOVE ROUTE", route)
            tbl, destPrefix, prefix_len = routePrefix(route)
            rtlremist.append(routeMatch(nh, tbl, destPrefix, prefix_len))

        rtlist = []

        for route in changed_routes.changed():
            if debug:
                print("CHANGE ROUTE", route, ":", new_routes[route])
            tbl, destPrefix, prefix_len = routePrefix(route)
            # remove the route using cookie 0, to remove all paths
            rtremlist.append(routeMatch(nh, tbl, destPrefix, prefix_len))
            # Build the route table objects for each next hop
            # once the BGP JET API supports multiple next hops per route, this can be
            # replaced with a single rpc call
            for nh in new_routes[route]:
                rtlist.append(
                    routeEntry(nh, tbl, destPrefix, prefix_len))

        for route in changed_routes.added():
            if debug:
                print("ADD ROUTE", route, ":", new_routes[route])
            tbl, destPrefix, prefix_len = routePrefix(route)
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
                print("BgpRouteRemove failed with code", result.status)
            else:
                print("routes successfully removed")

        if len(rtlist) > 0:
            routeUpdReq = bgp_route_service_pb2.BgpRouteUpdateRequest(
                bgp_routes=rtlist)
            result = bgp.BgpRouteUpdate(routeUpdReq, _JET_TIMEOUT)
            if result.status > bgp_route_service_pb2.BgpRouteOperReply.SUCCESS:
                print("BgpRouteAdd failed with code", result.status)
            else:
                print("routes successfully updated")

        old_routes = new_routes
        data = ''
        time.sleep(5)


if __name__ == '__main__':
    main()
