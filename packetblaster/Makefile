# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

all: build

build: 
	docker build -t packetblaster .

run:
	docker run -ti --rm --privileged -v ${PWD}:/root \
	  --name packetblaster --hostname packetblaster packetblaster

lwaftr1.conf: binding_table.txt
	@sed -e '/binding_table.txt/ {' -e 'r binding_table.txt' -e 'd' -e '}' \
	template.conf > lwaftr1.conf

binding_table.txt:
	docker run -ti --rm --entrypoint=/usr/local/bin/snabb snabb \
	lwaftr generate-binding-table 193.5.1.100 3 fc00::100 2001:db8::100 6 \
	| tr -d '\r' > binding_table.txt


sh:
	docker run -ti --rm --entrypoint=/bin/sh snabb

clean:
	rm lwaftr1.conf binding_table.txt || true
	docker system prune -f
