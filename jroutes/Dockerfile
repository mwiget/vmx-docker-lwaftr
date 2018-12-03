# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

ARG ALPINE_VERSION=3.8

FROM alpine:${ALPINE_VERSION} AS snabb

ENV SNABB_REPO "https://github.com/mwiget/snabb.git"
ENV SNABB_BRANCH "passthru"

RUN apk add --no-cache libgcc alpine-sdk gcc libpcap-dev linux-headers findutils \
  && git clone --branch ${SNABB_BRANCH} ${SNABB_REPO} && cd snabb && make -j

FROM alpine:${ALPINE_VERSION} as build
RUN apk add --no-cache build-base git go-bootstrap go protobuf \
  && go get github.com/golang/protobuf/proto \
  && go get github.com/golang/protobuf/protoc-gen-go \
  && go get github.com/Juniper/go-netconf/netconf \
  && go get google.golang.org/grpc \
  && go get github.com/eclipse/paho.mqtt.golang \
  && mkdir -p /root/go/src/github.com/vmx-docker-lwaftr/jroutes

COPY . /root/go/src/github.com/Juniper/vmx-docker-lwaftr/jroutes

RUN cd /root/go/src/github.com/Juniper/vmx-docker-lwaftr/jroutes \
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

RUN cd / && go build github.com/Juniper/vmx-docker-lwaftr/jroutes && strip jroutes

# Build main image

FROM alpine:${ALPINE_VERSION} 
RUN apk add --no-cache libgcc 

COPY --from=build /jroutes /bin
COPY --from=snabb /snabb/src/snabb /bin
COPY /simulator /simulator

WORKDIR /u

ENTRYPOINT ["/bin/jroutes"]
