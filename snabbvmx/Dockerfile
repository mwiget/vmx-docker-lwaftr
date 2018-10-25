# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

FROM ubuntu:18.04 AS proto
RUN apt-get update && apt-get install -y python protobuf-compiler-grpc
COPY /proto /proto
RUN mkdir grpc-py \
  && protoc --proto_path=proto --python_out=grpc-py --grpc_out=grpc-py \
  --plugin=protoc-gen-grpc=/usr/bin/grpc_python_plugin proto/*proto \
  && ls -l /grpc-py

FROM alpine:3.8 AS grpc
RUN apk add --no-cache \
  py2-pip gcc g++ linux-headers make musl-dev python-dev \
  && pip install protobuf grpcio

FROM alpine:3.8
RUN apk add --no-cache tini libgcc python libstdc++ py2-paho-mqtt py2-requests
COPY --from=proto /grpc-py /usr/lib/python2.7/
COPY --from=grpc /usr/lib/python2.7/site-packages /usr/lib/python2.7/site-packages/

VOLUME /u
WORKDIR /u

ENTRYPOINT ["/bin/ash"]
#ENTRYPOINT ["/sbin/tini", "/usr/bin/python", "/jroutes_noping.py"]
