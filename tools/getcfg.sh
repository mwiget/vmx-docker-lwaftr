#!/bin/bash
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

for vmx in vmx1 ; do
  IP=$(docker-compose logs $vmx |grep 'root password '|cut -d\( -f2|cut -d\) -f1)
  echo "$vmx ($IP)..."
  mv $vmx.conf.txt $vmx.old.txt 2>/dev/null
  ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $IP "show conf | find apply-groups " > $vmx.conf
  ls -l $vmx.conf
done

