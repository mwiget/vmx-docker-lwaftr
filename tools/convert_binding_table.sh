#!/usr/bin/env bash
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

if [ -z $1 ]; then
  cat <<EOF

  $0 <newstyle softwire config file>

  input file format example:

  $ cat snabb-60k.conf
  softwire-config {
  binding-table {
    softwire { ipv4 193.5.1.100; psid 1; b4-ipv6 2001:db8::100; br-address fc00::100; port-set { psid-length 6; }}
    softwire { ipv4 193.5.1.100; psid 2; b4-ipv6 2001:db8::101; br-address fc00::100; port-set { psid-length 6; }}
    softwire { ipv4 193.5.1.100; psid 3; b4-ipv6 2001:db8::102; br-address fc00::100; port-set { psid-length 6; }}
    softwire { ipv4 193.5.1.100; psid 4; b4-ipv6 2001:db8::103; br-address fc00::100; port-set { psid-length 6; }}
    softwire { ipv4 193.5.1.100; psid 5; b4-ipv6 2001:db8::104; br-address fc00::100; port-set { psid-length 6; }}
    . . .
  }

  will be converted into this:

  $ $0 snabb-60k.conf
  apply-macro softwires_fc00::100
  2001:db8::100 193.5.1.100,1,6,0
  2001:db8::101 193.5.1.100,2,6,0
  2001:db8::102 193.5.1.100,3,6,0
  2001:db8::103 193.5.1.100,4,6,0
  2001:db8::104 193.5.1.100,5,6,0
  . . . 

EOF
  exit 1
fi

grep psid $1 | head -1 | awk -F'[ {};]' '{print "apply-macro softwires_" $16}'
grep psid $1 | awk -F'[ {};]' '{print $13 " " $7 "," $10 "," $22 ",0"}'
