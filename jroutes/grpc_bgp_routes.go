// Copyright (c) 2018, Juniper Networks, Inc.
// All rights reserved.

package main

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"reflect"
	"strconv"
	"strings"

	"google.golang.org/grpc"

	authentication "github.com/juniper/vmx-docker-lwaftr/jroutes/stubs/authentication"
	jnx_addr "github.com/juniper/vmx-docker-lwaftr/jroutes/stubs/jnx_addr"
	routing "github.com/juniper/vmx-docker-lwaftr/jroutes/stubs/routing"
)

// GrpcSession contains gRPC connection handle
type GrpcSession struct {
	conn       *grpc.ClientConn
	cbgp       routing.BgpRouteClient
	oldRoutes  map[string][]string
	ipv4prefix int
	ipv6prefix int
}

// GrpcDial opens gRPC session to host
func (g *GrpcSession) GrpcDial(host *string, grpcPort int, user *string, id *string, ipv4prefix int, ipv6prefix int) bool {

	var opts []grpc.DialOption

	log.SetFlags(log.LstdFlags)

	g.oldRoutes = make(map[string][]string)
	g.ipv4prefix = ipv4prefix
	g.ipv6prefix = ipv6prefix
	g.cbgp = nil

	pwd, err := ioutil.ReadFile("." + *host + ".pwd")
	if err != nil {
		log.Fatalf("password file missing: ." + *host + ".pwd")
		return (false)
	}
	pwdStr := strings.TrimSuffix(string(pwd), "\r\n")

	hostname := *host + ":" + strconv.Itoa(grpcPort)

	opts = append(opts, grpc.WithInsecure())
	conn, err := grpc.Dial(hostname, opts...)
	if err != nil {
		log.Fatalf("Could not connect via gRPC to %s: %s", hostname, err)
		return (false)
	}
	g.conn = conn

	l := authentication.NewLoginClient(g.conn)
	dat, err := l.LoginCheck(context.Background(),
		&authentication.LoginRequest{UserName: *user, Password: pwdStr, ClientId: *id})

	if err != nil {
		log.Fatalf("Authentication failed for user %s with password %s: %s", *user, pwdStr, err)
		return (false)
	}
	log.Printf("gRPC authenticated to %s as %s", hostname, *user)

	return dat.Result
}

// BuildRoute returns prefix, len and table from a given ip route string with the correct types
func BuildRoute(routeStr string, ipv4prefix int, ipv6prefix int) (route routing.RoutePrefix, prefix uint32, routeTable routing.RouteTable) {

	var routeAddrString jnx_addr.IpAddress_AddrString
	routeAddrString.AddrString = routeStr

	var routeIPAddr jnx_addr.IpAddress
	routeIPAddr.AddrFormat = &routeAddrString

	var rtTableName routing.RouteTableName
	var routePrefix routing.RoutePrefix
	var prefixLen uint32

	ip := net.ParseIP(routeStr)
	if ip.To4() != nil {
		rtTableName.Name = "inet.0"
		var routePrefixInet routing.RoutePrefix_Inet
		routePrefixInet.Inet = &routeIPAddr
		routePrefix.RoutePrefixAf = &routePrefixInet
		prefixLen = uint32(ipv4prefix)
	} else {
		rtTableName.Name = "inet6.0"
		var routePrefixInet routing.RoutePrefix_Inet6
		routePrefixInet.Inet6 = &routeIPAddr
		routePrefix.RoutePrefixAf = &routePrefixInet
		prefixLen = uint32(ipv6prefix)
	}

	var rtTableFormat routing.RouteTable_RttName
	rtTableFormat.RttName = &rtTableName

	var rtTable routing.RouteTable
	rtTable.RtTableFormat = &rtTableFormat

	return routePrefix, prefixLen, rtTable
}

// UpdateRoutes in BGP with multiple next-hop after comparing with last update
func (g *GrpcSession) UpdateRoutes(rt *ipmap, nh *ipmap) bool {

	var v4nh []string
	var v6nh []string

	newRoutes := make(map[string][]string)

	// separate v4 from v6 next hops into slices
	for nexthop := range *nh {
		ip := net.ParseIP(nexthop)
		if ip.To4() != nil {
			v4nh = append(v4nh, nexthop)
		} else {
			v6nh = append(v6nh, nexthop)
		}
	}

	fmt.Println("v4 next-hops:", v4nh)
	fmt.Println("v6 next-hops:", v6nh)

	// attach next-hops to unique routes based on inet family
	for route := range *rt {
		ip := net.ParseIP(route)
		if ip.To4() != nil {
			newRoutes[route] = v4nh
		} else {
			newRoutes[route] = v6nh
		}
	}

	fmt.Println("new routes with next-hops:", newRoutes)

	if reflect.DeepEqual(newRoutes, g.oldRoutes) {
		log.Println("no change in routes or next-hop detected")
		return true
	}

	if g.cbgp != nil {
		// cleanup first
		c := g.cbgp
		var bgpRouteCleanupRequest routing.BgpRouteCleanupRequest
		cleanup, err := c.BgpRouteCleanup(context.Background(), &bgpRouteCleanupRequest)
		if err != nil {
			log.Fatalf("BgpRouteCleanup failed: %v", err)
			return false
		}
		g.cbgp = nil
		log.Printf("BgpRouteCleanup %v", cleanup.Status)
	}

	c := routing.NewBgpRouteClient(g.conn)

	var bgpRouteInit routing.BgpRouteInitializeRequest
	_, err := c.BgpRouteInitialize(context.Background(), &bgpRouteInit)
	if err != nil {
		log.Fatalf("BGP route service initialization failed: %s", err)
		return (false)
	}
	g.cbgp = c
	log.Println("BGP route service initialized.")

	var bgpRouteUpdateReq routing.BgpRouteUpdateRequest

	for route := range newRoutes {
		routePrefix, prefixLen, routeTable := BuildRoute(route, g.ipv4prefix, g.ipv6prefix)

		// only single nh per route supported today, hence we create multiple route entries per nh
		for i := range newRoutes[route] {
			var bgpRouteEntry routing.BgpRouteEntry
			bgpRouteEntry.DestPrefix = &routePrefix
			bgpRouteEntry.DestPrefixLen = prefixLen
			bgpRouteEntry.Table = &routeTable
			bgpRouteEntry.Protocol = routing.RouteProtocol_PROTO_BGP_STATIC
			bgpRouteEntry.PathCookie = uint64(i)
			bgpRouteEntry.RouteType = routing.BgpPeerType_BGP_INTERNAL
			var nhAddrString jnx_addr.IpAddress_AddrString
			nhAddrString.AddrString = newRoutes[route][i]
			var nhIPAddr jnx_addr.IpAddress
			nhIPAddr.AddrFormat = &nhAddrString
			bgpRouteEntry.ProtocolNexthops = append(bgpRouteEntry.ProtocolNexthops, &nhIPAddr)
			bgpRouteUpdateReq.BgpRoutes = append(bgpRouteUpdateReq.BgpRoutes, &bgpRouteEntry)
			if strings.Contains(route, ":") {
				log.Printf("Inet6 %v Prefix: %s", bgpRouteEntry.GetTable().GetRttName(), bgpRouteEntry.GetDestPrefix().GetInet6())
			} else {
				log.Printf("Inet  %v Prefix: %s", bgpRouteEntry.GetTable().GetRttName(), bgpRouteEntry.GetDestPrefix().GetInet())
			}
		}
	}
	r, err := c.BgpRouteAdd(context.Background(), &bgpRouteUpdateReq)
	if err != nil {
		log.Fatalf("Couldn't send RPC: %v", err)
		return false
	}

	log.Printf("Status: %v", r.Status)
	log.Printf("OperationsCompleted: %d", r.OperationsCompleted)

	return true
}
