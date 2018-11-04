# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

ARG ALPINE_VERSION=3.8

FROM alpine:${ALPINE_VERSION} AS snabb

ENV SNABB_REPO "https://github.com/mwiget/snabb.git"
ENV SNABB_BRANCH "passthru"

RUN apk add --no-cache libgcc alpine-sdk gcc libpcap-dev linux-headers findutils \
  && git clone --branch ${SNABB_BRANCH} ${SNABB_REPO} && cd snabb && make -j

FROM alpine:${ALPINE_VERSION}
RUN apk add --no-cache libgcc tcpdump iproute2

COPY --from=snabb /snabb/src/snabb /bin/
COPY launch.sh /

WORKDIR /u

ENTRYPOINT ["/bin/sh", "/launch.sh"]
