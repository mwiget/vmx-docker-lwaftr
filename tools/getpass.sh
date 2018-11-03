#!/bin/bash
# Copyright (c) 2017, Juniper Networks, Inc.
# All rights reserved.
#
# simple script to extract root passwords from vmx log file


list="vmx1 dcgw"
echo $list
for vmx in $list; do
  descr=$(docker logs $vmx | grep 'root password' | cut -d' ' -f1-4,7 | tr -d '\r' || echo $vmx)
  if [ ! -z "$descr" ]; then
    ip=$(docker logs $vmx | grep 'root password'|cut -d\( -f2|cut -d\) -f1)
    fpcmem=$(ssh -o StrictHostKeyChecking=no -o ConnectTimeout=1 $ip show chassis fpc 0 2>/dev/null | grep Online | awk '{print $9}')
    fpcmem="${fpcmem:-0}"
    if [ "$fpcmem" -gt "1024" ]; then
      success=$(($success + 1))
      echo -e "$descr \t ready"
    else
      echo -e "$descr \t ..."
    fi
  fi
done
