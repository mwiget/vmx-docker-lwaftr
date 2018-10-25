#!/bin/ash
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

while :
do
  echo "Listening on TCP port $PORT ..."
  nc -lk -p $PORT -e snabb $@
  echo "snabb terminated. Restarting in 5 seconds ..."
  sleep 5
done

