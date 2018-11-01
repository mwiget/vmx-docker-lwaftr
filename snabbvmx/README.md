# snabbvmx container

This container connects to vMX via gRPC and MQTT to retrieve the softwire configuration,
triggered by a commit event and configures snabb lwaftr accordingly.

It also retrieves the running snabb lwaftr configuration, extracts routes with nexthops and
injects these into BGP as static routes via the Junos JET API.


