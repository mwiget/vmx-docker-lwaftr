# snabbvmx container

This container runs snabbvmx.py to subscribe to commit events via MQTT and retrieve the softwire configuration via 
netconf, triggered by a commit event. This config is used to provision Snabb lwaftr.

It also retrieves the running snabb lwaftr configuration, extracts routes with nexthops and
injects these into BGP as static routes via the Junos JET API over gRPC.

The container is based on Alpine and includes Python3, gRPC, PyEz, Snabb and of course snabbvmx.py. The 
container size is rather small with less than 100 MBytes:

```
$ docker images | head -2
REPOSITORY                           TAG                 IMAGE ID            CREATED             SIZE
vmx-docker-lwaftr_snabbvmx           latest              89a82e674176        26 minutes ago      96.2MB
```

Example run:

```
$ docker logs -f vmx-docker-lwaftr_snabbvmx_1
2018-11-02 12:23:28,202 - INFO - connecting to vmx1 mqtt port 1883 ...
2018-11-02 12:23:28,203 - INFO - connecting to vmx1 gRPC port 50051 ...
2018-11-02 12:23:28,230 - INFO - gRPC Login successful
2018-11-02 12:23:28,232 - INFO - Successfully connected to BGP Route Service on vmx1
2018-11-02 12:23:28,420 - INFO - received 6 lwaftr routes with 4 (out of 4) reachable next hops
2018-11-02 12:23:28,432 - INFO - BgpRouteAdd routes successfully updated
2018-11-02 12:23:28,432 - INFO - Connected with result code 0
2018-11-02 12:23:28,432 - INFO - subscribed to UI_COMMIT_COMPLETED
2018-11-02 12:23:28,621 - INFO - received 6 lwaftr routes with 4 (out of 4) reachable next hops
2018-11-02 12:23:28,811 - INFO - received 6 lwaftr routes with 4 (out of 4) reachable next hops
2018-11-02 12:23:29,003 - INFO - received 6 lwaftr routes with 4 (out of 4) reachable next hops
```
