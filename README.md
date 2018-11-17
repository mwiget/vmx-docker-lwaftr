
## Generate binding table

The following command generates a binding table with 6300 entries for shared
IPv4 adddresses 192.0.2.1 thru 192.0.2.100 (from address block reserved for documentation, RFC 5737).

```
$ sudo snabb/src/snabb lwaftr generate-configuration --output lw.conf 192.0.2.1 100 fc00::100 2001:db8::1 6
$ grep psid lw.conf |wc -l
63000
```
