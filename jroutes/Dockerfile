# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

ARG ALPINE_VERSION=3.8

FROM alpine:${ALPINE_VERSION} AS snabb

ENV SNABB_REPO "https://github.com/mwiget/snabb.git"
ENV SNABB_BRANCH "passthru"

RUN apk add --no-cache libgcc alpine-sdk gcc libpcap-dev linux-headers findutils \
  && git clone --branch ${SNABB_BRANCH} ${SNABB_REPO} && cd snabb && make -j

FROM alpine:${ALPINE_VERSION}
# libc6-compat 
RUN apk add --no-cache build-base git go-bootstrap go protobuf \
  && go get github.com/golang/protobuf/proto \
  && go get github.com/golang/protobuf/protoc-gen-go \
  && go get github.com/Juniper/go-netconf/netconf \
  && go get google.golang.org/grpc \
  && mkdir -p /root/go/src/github.com/vmx-docker-lwaftr/jroutes

COPY . /root/go/src/github.com/vmx-docker-lwaftr/jroutes

RUN cd /root/go/src/github.com/vmx-docker-lwaftr/jroutes \
  && export PATH=${PATH}:/root/go/bin \
  && mkdir -p stubs \
  && mkdir -p stubs/authentication \
  && mkdir -p stubs/bgp_route \
  && mkdir -p stubs/jnx_addr \
  && mkdir -p stubs/prpd_common \
  && mkdir -p stubs/agent \
  && protoc -I proto --go_out=plugins=grpc:stubs/authentication proto/authentication_service.proto \
  && protoc -I proto --go_out=plugins=grpc:stubs/bgp_route proto/bgp_route_service.proto \
  && protoc -I proto --go_out=plugins=grpc:stubs/jnx_addr proto/jnx_addr.proto \
  && protoc -I proto --go_out=plugins=grpc:stubs/prpd_common proto/prpd_common.proto 

#COPY --from=proto /grpc-py /usr/lib/python3.6/
#COPY --from=grpc /grpc/lib /usr/lib

COPY --from=snabb /snabb/src/snabb /bin
COPY /simulator /simulator

#ENV GOPATH=/root/go
ENV PATH=${PATH}:/root/go/bin

WORKDIR /u

ENTRYPOINT ["/bin/ash"]
