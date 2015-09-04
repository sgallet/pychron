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
from pychron.core.ui import set_qt

set_qt()
# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.logger_setup import logging_setup
from pychron.hardware.core.core_device import CoreDevice


class TempHumMicroServer(CoreDevice):
    scan_func = 'read_temperature'

    def read_temperature(self, **kw):
        v = self.ask('*SRTF', **kw)
        return self._parse_response(v)

    def read_humidity(self, **kw):
        v = self.ask('*SRH', **kw)
        return self._parse_response(v)

    def _parse_response(self, v):
        try:
            return float(v)
        except (AttributeError, ValueError, TypeError):
            return self.get_random_value()

if __name__ == '__main__':
    logging_setup('eprobe')
    dev = TempHumMicroServer(name='microserver')
    dev.bootstrap()
    dev.get_temperature()

# ============= EOF =============================================



