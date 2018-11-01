# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

# replace ubuntu with Alpine once package grpc becomes available (currently in testing)
FROM ubuntu:18.04 AS proto
RUN apt-get update && apt-get install -y python3 protobuf-compiler-grpc
COPY /proto /proto
RUN mkdir grpc-py \
  && protoc --proto_path=proto --python_out=grpc-py --grpc_out=grpc-py \
    --plugin=protoc-gen-grpc=/usr/bin/grpc_python_plugin proto/*proto \
  && echo "generated grpc python code in /grpc-py: " && ls -l /grpc-py

FROM alpine:3.8 AS grpc
RUN apk add --no-cache gcc g++ linux-headers \
    make musl-dev python3-dev \
    && pip3 install --install-option="--prefix=/grpc" \
    --ignore-installed protobuf grpcio

FROM snabb:latest AS snabb

FROM alpine:3.8
RUN apk add --no-cache libgcc python3 libstdc++ \
    py3-netaddr py3-paho-mqtt py3-lxml py3-jinja2 py3-six py3-paramiko py3-cffi \
    && pip3 install junos-eznc \
    && rm -rf /usr/lib/python3*/site-packages/pip /usr/lib/python3*/__pycache__ \
    && rm -rf /usr/share/terminfo

#    && pip3 install pyyaml junos-eznc 

COPY --from=proto /grpc-py /usr/lib/python3.6/
COPY --from=grpc /grpc/lib /usr/lib

COPY --from=snabb /usr/local/bin/snabb /bin/
COPY snabbvmx.py /

WORKDIR /u

ENTRYPOINT ["/usr/bin/python3", "snabbvmx.py"]
