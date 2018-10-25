#!/bin/ash
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

echo "creating $LINKCOUNT links ..."
# xe interfaces will be consumed by vMX
for n in $(seq $LINKCOUNT)
do
  m=$(($n - 1))
  ip link add xe$m type veth
  ip link set veth0 name int$m
  ifconfig xe$m mtu 9100 up
  ifconfig int$m mtu 9100 up
  ip link show dev xe$m
done
