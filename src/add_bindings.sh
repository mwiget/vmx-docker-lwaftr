#!/usr/bin/env bash
# Copyright (c) 2017, Juniper Networks, Inc.
# All rights reserved.

BINDINGS=$1

if [ ! -f "$BINDINGS" ]; then
  echo "no binding file found at $BINDINGS"
  echo "Usage: $0 binding-file"
  exit 1
fi

# vRE might not be up for a while, so keep trying to upload the license file ...
while true; do
  scp -o StrictHostKeyChecking=no $BINDINGS root@128.0.0.1:/var/db/scripts/commit/
  if [ $? == 0 ]; then
    echo "transfer successful"
    break;
  fi
  echo "binding upload failed ($?), sleeping 5 seconds ..."
  sleep 5
done
