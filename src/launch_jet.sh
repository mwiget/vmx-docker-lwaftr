#!/bin/bash
# Copyright (c) 2017, Juniper Networks, Inc.
# All rights reserved.

echo "$0: Launching jet server"
while :
do
  python /jet/main.py
  echo "JET terminated. Restarting in 5 seconds ..."
  sleep 5
done
