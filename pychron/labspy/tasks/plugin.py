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
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
# from pychron.labspy.client import MeteorLabspyClient
from pychron.labspy.client import LabspyClient
from pychron.labspy.tasks.preferences import LabspyPreferencesPane


class LabspyClientPlugin(BaseTaskPlugin):
    name = 'LabspyClient'
    id = 'pychron.labspy_client.plugin'

    def _labspy_client_factory(self, *args, **kw):
        return LabspyClient()

    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=LabspyClient,
                                        factory=self._labspy_client_factory)
        return [so]

    def _preferences_panes_default(self):
        return [LabspyPreferencesPane]

    def test_communication(self):
        lc=self.application.get_service(LabspyClient)
        return lc.test_connection(warn=False)
# ============= EOF =============================================



