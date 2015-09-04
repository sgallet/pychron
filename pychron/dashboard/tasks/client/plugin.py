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
from apptools.preferences.preference_binding import bind_preference
from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.dashboard.client import DashboardClient
from pychron.dashboard.tasks.client.preferences import DashboardClientPreferencesPane, \
    ExperimentDashboardClientPreferencesPane
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin


class DashboardClientPlugin(BaseTaskPlugin):
    dashboard_client = Instance(DashboardClient)

    # def _tasks_default(self):
    #     return [TaskFactory(id='pychron.dashboard.server',
    #                         name='Dashboard Server',
    #                         accelerator='Ctrl+4',
    #                         factory=self._factory)]
    #
    # def _factory(self):
    #     f = DashboardServerTask(server=self.dashboard_server)
    #     return f

    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=DashboardClient,
                                        factory=self._client_factory)
        return [so]

    def _client_factory(self):
        client = DashboardClient()
        bind_preference(client, 'host', 'pychron.dashboard.client.host')
        bind_preference(client, 'port', 'pychron.dashboard.client.port')

        client.connect()
        client.load_configuration()
        client.listen()

        return client

    def start(self):
        pass
        # self.dashboard_client = DashboardServer(application=self.application)
        # s = self.dashboard_server
        # s.activate()

    def stop(self):
        pass
        # self.dashboard_server.deactivate()

    def _preferences_panes_default(self):
        ps = [DashboardClientPreferencesPane]
        if self.application.get_plugin('pychron.experiment.plugin'):
            ps.append(ExperimentDashboardClientPreferencesPane)
        return ps

# ============= EOF =============================================
