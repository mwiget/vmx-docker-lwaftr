#!/bin/sh
# Copyright (c) 2018, Juniper Networks, Inc.
# All rights reserved.

exec 2>/dev/null    # mute stderr
exec /usr/bin/python3 /snabbvmx.py $@
