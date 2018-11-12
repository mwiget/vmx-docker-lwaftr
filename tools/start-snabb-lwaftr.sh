#!/bin/bash
# Copyright (c) 2018, Juniper Networks, Inc.
# # All rights reserved.
#

CONTAINER=vmx1
LINKCOUNT=8
CONFIG=snabb-190.conf

pid=$(docker inspect -f "{{.State.Pid}}" $CONTAINER)
if [ -z "$pid" ]; then
    echo "Can't find pid for container $CONTAINER"
    sleep 2
    exit 1
fi

while :; do
  echo "extracting runtime root password into .$CONTAINER.pwd"
  docker logs $CONTAINER | grep 'root password' | awk 'NF>1{print $NF}' > .$CONTAINER.pwd
  if [ -s .$CONTAINER.pwd ]; then
    break
  fi
  echo "trying again in 5 seconds ..."
  sleep 5
done

sudo mkdir -p /var/run/netns 2>/dev/null
sudo ln -sf /proc/$pid/ns/net /var/run/netns/$CONTAINER
for n in $(seq $LINKCOUNT)
do
  m=$(($n - 1))
  mac=$(sudo ip netns exec $CONTAINER ifconfig xe$m |grep ether|awk '{print $2}')
  export eval macxe$m=$mac
done
envsubst < $CONFIG > $CONFIG.run
while :; do
  sudo ip netns exec $CONTAINER snabb/src/snabb lwaftr run --conf $CONFIG.run -n lwaftr
  echo "restarting snabb in 5 seconds ..."
sleep 5
done
