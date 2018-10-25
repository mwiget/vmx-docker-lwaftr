## jroutes Container

The multi-stage Dockerfile compiles protofiles found in the [proto](proto) folder and adds gRPC Python support.

The jroutes.py file uses the rib services to add static routes learned from snabb and jroutes_bgp.py is [wip] to use the bgp services api. 

BgpRouteAdd.py is an example app that uses the bgp services api and does work against the crr if using TCP port 40041 without authentication.

To build, run make:

```
$ make
. . .
Successfully built c5e007a10034
Successfully tagged jroutes:latest
```

```
$ docker images |grep jroutes
jroutes                  latest              c5e007a10034        2 hours ago         79.4MB
```

The Junos proto file for JET can be downloaded from [https://www.juniper.net/support/downloads/?p=jet#sw](https://www.juniper.net/support/downloads/?p=jet#sw), but the relevant files are already taken from the 17.4 IDL file and placed in the folder [proto](proto).

BTW this works well on (corporate) laptops too, thanks to Docker for OS/X and Windows.

## References

[BGP Route Services JET API 17.4](https://www.juniper.net/documentation/en_US/jet17.4/information-products/pathway-pages/bgp_route_service.html)
