package main

import (
	"encoding/xml"
	"io/ioutil"
	"log"
	"strings"

	"github.com/Juniper/go-netconf/netconf"
	"golang.org/x/crypto/ssh"
)

// Bfdsessions returns map of networks as key
type Bfdsessions struct {
	net ipmap
}

// BFDSessionInformation Element
type BFDSessionInformation struct {
	Session []BFDSession `xml:"bfd-session" json:"sessions,omitempty"`
}

// BFDSession Element
type BFDSession struct {
	Neighbor             string  `xml:"session-neighbor"`
	State                string  `xml:"session-state"`
	Interface            string  `xml:"session-interface"`
	DetectionTime        float64 `xml:"session-detection-time"`
	TransmissionInterval float64 `xml:"session-transmission-interval"`
	AdaptiveMultiplier   float64 `xml:"session-adaptive-multiplier"`
}

// BfdFetch grabs BFD sessions and populate network in b.net when State == Up
func (b *Bfdsessions) BfdFetch(host *string, user *string, ipmask *ipmask) int {

	var config *ssh.ClientConfig

	log.SetFlags(log.LstdFlags)

	b.net = make(ipmap)

	pwd, err := ioutil.ReadFile("." + *host + ".pwd")
	if err != nil {
		panic("password file missing: ." + *host + ".pwd")
	}
	pwdStr := strings.TrimSuffix(string(pwd), "\r\n")
	config = netconf.SSHConfigPassword(*user, pwdStr)

	n, err := netconf.DialSSH(*host, config)
	if err != nil {
		log.Fatal(err)
	}
	defer n.Close()

	//		log.Println("getting bfd session information")
	reply, err := n.Exec(netconf.RawMethod("<get-bfd-session-information/>"))
	if err != nil {
		panic(err)
	}
	//	log.Println("bfd info:", reply)
	bfdSession := BFDSessionInformation{}

	err = xml.Unmarshal([]byte(reply.Data), &bfdSession)
	if err != nil {
		log.Print(err)
	}

	for _, value := range bfdSession.Session {
		if value.State == "Up" {
			b.net[ipmask.Mask(value.Neighbor)]++
			//	log.Printf("Neighbor=%s State=%s net=%s\n", value.Neighbor, value.State, ipmask.Mask(value.Neighbor))
		} else {
			//log.Printf("Neighbor=%s State=%s (skipped)\n", value.Neighbor, value.State)
		}
	}
	return (0)
}
