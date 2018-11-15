# jroutes container

[wip]

Working jroutes container uses just 20 Mbytes:

```
$ docker images |head -2
REPOSITORY                           TAG                 IMAGE ID            CREATED             SIZE
vmx-docker-lwaftr_jroutes            latest              859f16725848        56 seconds ago      20.4MB
```


Example run with a bgp flap (clear bgp neighbor x) triggering bfd session flap and mqtt events:

```
/u # jroutes
2018/11/15 21:02:15 gRPC authenticated to vmx1:50051 as root
2018/11/15 21:02:15 subscribed via MQTT to vmx1
2018/11/15 21:02:15 active next-hop: 2001:db8::100
2018/11/15 21:02:15 active next-hop: 172.20.1.101
2018/11/15 21:02:15 active next-hop: 2001:db8:1::101
2018/11/15 21:02:15 active next-hop: 172.20.0.100
v4 next-hops: [172.20.1.101 172.20.0.100]
v6 next-hops: [2001:db8:1::101 2001:db8::100]
new routes with next-hops: map[fc00:::[2001:db8:1::101 2001:db8::100] 193.5.1.96:[172.20.1.101 172.20.0.100] 2001:db8:::[2001:db8:1::101 2001:db8::100]]
2018/11/15 21:02:15 BGP route service initialized.
2018/11/15 21:02:15 Inet  name:"inet.0"  Prefix: addr_string:"193.5.1.96"
2018/11/15 21:02:15 Inet  name:"inet.0"  Prefix: addr_string:"193.5.1.96"
2018/11/15 21:02:15 Inet6 name:"inet6.0"  Prefix: addr_string:"2001:db8::"
2018/11/15 21:02:15 Inet6 name:"inet6.0"  Prefix: addr_string:"2001:db8::"
2018/11/15 21:02:15 Inet6 name:"inet6.0"  Prefix: addr_string:"fc00::"
2018/11/15 21:02:15 Inet6 name:"inet6.0"  Prefix: addr_string:"fc00::"
2018/11/15 21:02:15 Status: SUCCESS
2018/11/15 21:02:15 OperationsCompleted: 6
/u # cd /tmp; go build github.com/juniper/vmx-docker-lwaftr/jroutes && cd /u && /tmp/jroutes -d
2018/11/15 21:03:14 gRPC authenticated to vmx1:50051 as root
2018/11/15 21:03:14 subscribed via MQTT to vmx1
2018/11/15 21:03:14 active next-hop: 172.20.1.101
2018/11/15 21:03:14 active next-hop: 2001:db8:1::101
2018/11/15 21:03:14 active next-hop: 172.20.0.100
2018/11/15 21:03:14 active next-hop: 2001:db8::100
v4 next-hops: [172.20.0.100 172.20.1.101]
v6 next-hops: [2001:db8::100 2001:db8:1::101]
new routes with next-hops: map[193.5.1.96:[172.20.0.100 172.20.1.101] 2001:db8:::[2001:db8::100 2001:db8:1::101] fc00:::[2001:db8::100 2001:db8:1::101]]
2018/11/15 21:03:14 BGP route service initialized.
2018/11/15 21:03:14 Inet6 name:"inet6.0"  Prefix: addr_string:"2001:db8::"
2018/11/15 21:03:14 Inet6 name:"inet6.0"  Prefix: addr_string:"2001:db8::"
2018/11/15 21:03:14 Inet6 name:"inet6.0"  Prefix: addr_string:"fc00::"
2018/11/15 21:03:14 Inet6 name:"inet6.0"  Prefix: addr_string:"fc00::"
2018/11/15 21:03:14 Inet  name:"inet.0"  Prefix: addr_string:"193.5.1.96"
2018/11/15 21:03:14 Inet  name:"inet.0"  Prefix: addr_string:"193.5.1.96"
2018/11/15 21:03:14 Status: SUCCESS
2018/11/15 21:03:14 OperationsCompleted: 6
2018/11/15 21:03:18 incoming MQTT message: /junos/events/syslog/BFDD_TRAP_SHOP_STATE_DOWN
2018/11/15 21:03:19 active next-hop: 2001:db8::100
2018/11/15 21:03:19 active next-hop: 172.20.1.101
2018/11/15 21:03:19 active next-hop: 2001:db8:1::101
2018/11/15 21:03:19 active next-hop: 172.20.0.100
v4 next-hops: [172.20.1.101 172.20.0.100]
v6 next-hops: [2001:db8:1::101 2001:db8::100]
new routes with next-hops: map[193.5.1.96:[172.20.1.101 172.20.0.100] 2001:db8:::[2001:db8:1::101 2001:db8::100] fc00:::[2001:db8:1::101 2001:db8::100]]
2018/11/15 21:03:19 BgpRouteCleanup SUCCESS
2018/11/15 21:03:19 BGP route service initialized.
2018/11/15 21:03:19 Inet6 name:"inet6.0"  Prefix: addr_string:"fc00::"
2018/11/15 21:03:19 Inet6 name:"inet6.0"  Prefix: addr_string:"fc00::"
2018/11/15 21:03:19 Inet  name:"inet.0"  Prefix: addr_string:"193.5.1.96"
2018/11/15 21:03:19 Inet  name:"inet.0"  Prefix: addr_string:"193.5.1.96"
2018/11/15 21:03:19 Inet6 name:"inet6.0"  Prefix: addr_string:"2001:db8::"
2018/11/15 21:03:19 Inet6 name:"inet6.0"  Prefix: addr_string:"2001:db8::"
2018/11/15 21:03:19 Status: SUCCESS
2018/11/15 21:03:19 OperationsCompleted: 6
```
