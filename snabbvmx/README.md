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

