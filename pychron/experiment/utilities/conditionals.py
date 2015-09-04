# ===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pychron_constants import LINE_STR, NULL_STR, LIGHT_RED, LIGHT_YELLOW

SYSTEM = 10
QUEUE = 20
RUN = 30

LEVEL_TXT_MAP = {SYSTEM: 'system', QUEUE: 'queue', RUN: 'run'}
LEVEL_COLOR_MAP = {SYSTEM: LIGHT_RED, QUEUE: 'lightblue', RUN: LIGHT_YELLOW}

CONDITIONAL_GROUP_TAGS = ('action', 'cancelation', 'truncation', 'termination')


def level_text(l):
    return LEVEL_TXT_MAP.get(l, '')


def level_color(l):
    return LEVEL_COLOR_MAP.get(l, 'white')


def test_queue_conditionals_name(name):
    return bool(name and not name in ('Queue Conditionals', NULL_STR, LINE_STR))

# ============= EOF =============================================
