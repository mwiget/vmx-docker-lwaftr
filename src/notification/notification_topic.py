#!/usr/bin/env python
#
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
#
# Copyright (c) 2015 Juniper Networks, Inc.
# All rights reserved.
#
# Use is subject to license terms.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from common.mylogging import LOG

DEFAULT_VALUE = "+"                           # Implies any value
DEFAULT_TOPIC = "#"                           # Implies all value
DEFAULT_IFD = r"+/+/+"                        # Regular expression for a default IFD
GENPUB_TOPIC_HEADER = r"/junos/events/genpub" # Generic pub event topic header
CONFIG_UPDATE = r"config-update"

class CreateTopic(object):

    """
    Wrapper class for creating Notification Topic.

    """
    def create_config_update_topic(self):
        """
        This method creates a topic to subscribe config-update events.

        @return: Returns the config-update topic object

        """
        data = {}
        data['subscribed'] = 0
        data['topic'] = '%s/%s' % (GENPUB_TOPIC_HEADER, CONFIG_UPDATE)
        self.topics_subscribed.append(data['topic'])
        LOG.info('Successfully appended the topic %s' % data['topic'])
        return type('Topic', (), data)

