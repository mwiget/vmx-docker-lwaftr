// Copyright (c) 2018, Juniper Networks, Inc.
// All rights reserved.

package main

import (
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	mqtt "github.com/eclipse/paho.mqtt.golang"
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
	mqttPort := *flag.Int("mqtt_port", 1883, "MQTT broker port number")
	ipv4prefix := *flag.Int("ipv4mask", 29, "IPv4 route aggregate mask")
	ipv6prefix := *flag.Int("ipv6mask", 64, "IPv6 route aggregate mask")
	debugPtr := flag.Bool("d", false, "enable debugging")

	flag.Parse()

	log.SetFlags(log.LstdFlags)

	g := GrpcSession{}

	g.GrpcDial(targetPtr, grpcPort, userPtr, snabbIDPtr, ipv4prefix, ipv6prefix)

	ipmask := ipmask{}
	ipmask.Set(ipv4prefix, ipv6prefix)

	// MQTT client

	opts := mqtt.NewClientOptions()
	opts.AddBroker(fmt.Sprintf("tcp://%s:%d", *targetPtr, mqttPort))
	opts.SetClientID(*snabbIDPtr)
	choke := make(chan [2]string)
	opts.SetDefaultPublishHandler(func(client mqtt.Client, msg mqtt.Message) {
		choke <- [2]string{msg.Topic(), string(msg.Payload())}
	})
	client := mqtt.NewClient(opts)
	sToken := client.Connect()
	if sToken.Wait() && sToken.Error() != nil {
		log.Fatalf("Error on MQTT Client.Connect(): %v", sToken.Error())
		os.Exit(1)
	}
	filters := map[string]byte{
		"/junos/events/syslog/UI_COMMIT_COMPLETED":       0,
		"/junos/events/syslog/BFDD_TRAP_SHOP_STATE_UP":   1,
		"/junos/events/syslog/BFDD_TRAP_SHOP_STATE_DOWN": 2,
	}
	client.SubscribeMultiple(filters, nil)

	log.Printf("subscribed via MQTT to %s\n", *targetPtr)
	defer client.Disconnect(250)
	defer log.Println("MQTT Subscriber disconnected")

	sigs := make(chan os.Signal, 3)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)

	for {
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

		select {
		case incoming := <-choke:
			topic := incoming[0]
			log.Printf("incoming MQTT message: %s", topic)

		case c := <-sigs:
			if c == syscall.SIGINT || c == syscall.SIGTERM || c == syscall.SIGKILL {
				client.Disconnect(250)
				os.Exit(0)
			}
		}
	}
}
