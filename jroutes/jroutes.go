package main

import (
	"flag"
	"log"
	"net"
	"time"
)

type ipmap map[string]int

type ipmask struct {
	ipv4 net.IPMask
	ipv6 net.IPMask
}

func (ipmask *ipmask) Set(ipv4prefix int, ipv6prefix int) {
	ipmask.ipv4 = net.CIDRMask(ipv4prefix, 32)
	ipmask.ipv6 = net.CIDRMask(ipv6prefix, 128)
}

func (ipmask *ipmask) Mask(ipString string) string {
	ip := net.ParseIP(ipString)
	ipMasked := ip.Mask(ipmask.ipv4)
	if ip.To4() == nil {
		ipMasked = ip.Mask(ipmask.ipv6)
	}
	return ipMasked.String()
}

// Match next-hops with active bfd protected networks and remove unreachable
func dropUnreach(s *Snabbroutes, b *Bfdsessions, ipmask *ipmask) {
	for key := range s.nh {
		if !(b.net[ipmask.Mask(key)] > 0) {
			// invalid next hop
			delete(s.nh, ipmask.Mask(key))
		}
	}
}

func main() {

	targetPtr := flag.String("target", "vmx1", "Junos hostname or IP address")
	userPtr := flag.String("user", "root", "Junos user account for gRPC and Netconf")
	snabbIDPtr := flag.String("snabbid", "lwaftr", "snabb lwaftr id")
	grpcPort := *flag.Int("grpc_port", 50051, "gRPC port number")
	ipv4prefix := *flag.Int("ipv4mask", 29, "IPv4 route aggregate mask")
	ipv6prefix := *flag.Int("ipv6mask", 64, "IPv6 route aggregate mask")
	debugPtr := flag.Bool("d", false, "enable debugging")

	flag.Parse()

	log.SetFlags(log.LstdFlags)

	g := GrpcSession{}

	g.GrpcDial(targetPtr, grpcPort, userPtr, snabbIDPtr, ipv4prefix, ipv6prefix)

	ipmask := ipmask{}
	ipmask.Set(ipv4prefix, ipv6prefix)

	s := Snabbroutes{}
	s.SnabbFetch(snabbIDPtr, &ipmask)

	b := Bfdsessions{}
	b.BfdFetch(targetPtr, userPtr, &ipmask)

	// eliminate next-hops on links with bfd session in Down state
	dropUnreach(&s, &b, &ipmask)

	if *debugPtr {
		for key := range s.nh {
			log.Printf("active next-hop: %s\n", key)
		}
	}

	g.UpdateRoutes(&s.rt, &s.nh)
	log.Println("sleeping for 5 seconds, then run it again")
	time.Sleep(5 * time.Second)
	g.UpdateRoutes(&s.rt, &s.nh)
}
