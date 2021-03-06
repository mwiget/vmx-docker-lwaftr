#!/bin/bash
# Copyright (c) 2016, Juniper Networks, Inc.
# All rights reserved.

MGMTIP=$1
IDENTITY=$2
BINDINGS=$3

echo "$0: launching snabbvmx manager $MGMTIP $IDENTITY $BINDINGS"

if [ -z "$IDENTITY" ]; then
  echo "Usage: $0 management-ip-address identity.key"
  exit 1
fi

if [ -f "$BINDINGS" ]; then
  /add_bindings.sh $MGMTIP $IDENTITY $BINDINGS 
fi

while :
do
  MANAGER=/snabbvmx_manager.pl
  if [ -f /u/snabbvmx_manager.pl ]; then
     cp /u/snabbvmx_manager.pl /tmp/ 2>/dev/null
     MANAGER=/tmp/snabbvmx_manager.pl
  fi
  $MANAGER $MGMTIP $IDENTITY
  sleep 5
done
