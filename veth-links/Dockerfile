FROM alpine:3.7
RUN apk add --no-cache iproute2
COPY launch.sh /
ENTRYPOINT ["/bin/ash", "/launch.sh"]
