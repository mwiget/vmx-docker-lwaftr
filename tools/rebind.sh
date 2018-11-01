#!/bin/bash
echo -n  "0000:01:00.0" > /sys/bus/pci/drivers/ixgbe/bind # ens4f0
echo -n  "0000:01:00.1" > /sys/bus/pci/drivers/ixgbe/bind # ens4f1
echo -n  "0000:03:00.0" > /sys/bus/pci/drivers/ixgbe/bind # ens3f0
echo -n  "0000:03:00.1" > /sys/bus/pci/drivers/ixgbe/bind # ens3f1

echo -n "ens3f0 "
ethtool -i ens3f0 | grep bus-info | cut -d' ' -f2

echo -n "ens3f1 "
ethtool -i ens3f1 | grep bus-info | cut -d' ' -f2

echo -n "switch ens4f0 "
ethtool -i ens4f0 | grep bus-info | cut -d' ' -f2

echo -n "switch ens4f1 "
ethtool -i ens4f1 | grep bus-info | cut -d' ' -f2


