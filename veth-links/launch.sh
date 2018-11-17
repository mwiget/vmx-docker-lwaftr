#!/bin/ash
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.


MACS=$(grep -A7 passthru-interface /u/$SNABBCONFIG | grep mac | grep mac|awk '{print $2}'|cut -d\; -f1)
if [ -z "$MACS" ]; then
  echo "ERROR: No passthru-interfaces found in $SNABBCONFIG !"
  sleep 60
  exit 1
fi

echo "creating pass-thru links for $CONTAINER from snabb config $SNABBCONFIG"

# xe interfaces will be consumed by vMX
m=0
for MAC in $MACS
do
  ip link add xe$m type veth
  ip link set xe$m address $MAC
  ip link set veth0 name int$m
  ifconfig xe$m mtu 9100 up
  ifconfig int$m mtu 9100 up
  ip link show dev xe$m
  m=$(($m + 1))
done
echo "task completed."
tail -f /dev/null # equivalent to 'sleep forever' to keep this container alive
