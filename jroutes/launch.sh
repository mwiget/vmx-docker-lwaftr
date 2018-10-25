#!/bin/ash
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

echo "removing ipv4 and ipv6 default route"
ip route del default
ip -6 route del default

echo "adding default route via vmx1"
ip route add default via vmx1
ip -6 route add default via vmx1

python /jroutes.py $@
sleep 5555
