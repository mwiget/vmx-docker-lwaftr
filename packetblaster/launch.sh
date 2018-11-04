#!/bin/ash

echo "setting eth0 address to $LOCAL_IP"
ip address flush dev eth0
ip address add $LOCAL_IP dev eth0
ip address show dev eth0

while :
do
  ping -c 3 $DCGW_IP
  if [ 0 == $? ]; then
    break;
  fi
  echo "waiting for lwaftr to be reachable ..."
  sleep 5
done

echo "adding default route via dcgw $DCGW_IP"
ip route add default via $DCGW_IP

dstmac=$(arp -na | awk '{print $4}')
srcmac=$(ifconfig eth0|grep HWaddr|awk '{print $5}')
echo "srcmac=$srcmac -> dstmac=$dstmac"

echo /bin/snabb packetblaster lwaftr --src_mac $srcmac --dst_mac $dstmac --int eth0 $@
/bin/snabb packetblaster lwaftr --src_mac $srcmac --dst_mac $dstmac --int eth0 $myip $@
#/bin/ash
