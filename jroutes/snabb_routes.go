package main

import (
	"bufio"
	"log"
	"net"
	"os/exec"
	"strings"
)

// Snabbroutes contains route and next-hop maps
type Snabbroutes struct {
	rt, nh ipmap
}

// SnabbFetch grabs routes and next-hops from running lwaftr instance
func (s *Snabbroutes) SnabbFetch(snabbIDPtr *string, ipmask *ipmask) int {

	log.SetFlags(log.LstdFlags)
	snabbCmd := exec.Command("snabb", "config", "get", "-s", "snabb-softwire-v2", *snabbIDPtr, "/")
	cmdReader, err := snabbCmd.StdoutPipe()
	if err != nil {
		panic(err)
	}

	s.rt = make(ipmap)
	s.nh = make(ipmap)

	err = snabbCmd.Start()
	if err != nil {
		log.Println("Error starting snabbCmd", err)
		return (-1)
	}

	scanner := bufio.NewScanner(cmdReader)
	var skip = false
	for scanner.Scan() {
		t := strings.TrimSpace(scanner.Text())
		if skip == true {
			skip = false
			continue
		}
		if strings.Index(t, "next-hop") > -1 {
			skip = true
			continue
		}
		kv := strings.Fields(strings.Trim(t, ";"))
		if len(kv) == 2 {
			ip := kv[1]
			switch kv[0] {
			case "b4-ipv6":
				s.rt[ipmask.Mask(ip)]++
			case "ipv4":
				s.rt[ipmask.Mask(ip)]++
			case "br-address":
				s.rt[ipmask.Mask(ip)]++
			case "ip":
				ip := net.ParseIP(ip)
				s.nh[ip.String()]++
			}
		}
	}
	err = snabbCmd.Wait()

	if err != nil {
		log.Println("Error waiting for snabbCmd", err)
		return (-1)
	}

	//		log.Printf("%d Routes with %d nexthops\n", len(s.rt), len(s.nh))
	//		log.Println("Routes:", s.rt, " nexthops:", s.nh)

	return (0)
}
