#!/bin/bash
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

for vmx in vmx1 dcgw; do
  IP=$(docker-compose logs $vmx |grep 'root password '|cut -d\( -f2|cut -d\) -f1)
  echo "$vmx ($IP)..."
  ssh-keygen -f "$HOME/.ssh/known_hosts" -R "$IP"
done

