# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

FROM snabb:latest AS snabb

FROM alpine:3.8
RUN apk add --no-cache libgcc tcpdump \
    && mv /usr/sbin/tcpdump /sbin/tcpdump
COPY --from=snabb /usr/local/bin/snabb /usr/local/bin/

COPY launch.sh /
RUN chmod a+rx /*sh

VOLUME /u
WORKDIR /u

ENTRYPOINT ["/bin/ash", "/launch.sh"]
