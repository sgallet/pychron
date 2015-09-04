# ===============================================================================
# Copyright 2013 Jake Ross
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
from pychron.social.email.emailer import Emailer
from pychron.social.email.tasks.preferences import EmailPreferencesPane


class EmailPlugin(BaseTaskPlugin):
    id = 'pychron.email.plugin'
    name = 'Email'
    test_email_server_description = 'Test connection to the SMTP Email Server'
    def _email_factory(self):
        return Emailer()

    def _preferences_panes_default(self):
        return [EmailPreferencesPane]

    def _service_offers_default(self):
        so = self.service_offer_factory(factory=self._email_factory,
                                        protocol='pychron.social.email.emailer.Emailer')
        return [so]

    def test_email_server(self):
        e = self._email_factory()
        return e.test_email_server()

        # ============= EOF =============================================
