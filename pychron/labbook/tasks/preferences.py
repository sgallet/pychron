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
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traitsui.api import View, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.tasks.base_preferences_helper import GitRepoPreferencesHelper, test_connection_item, \
    remote_status_item


class LabBookPreferences(GitRepoPreferencesHelper):
    preferences_path = 'pychron.labbook'


class LabBookPreferencesPane(PreferencesPane):
    model_factory = LabBookPreferences
    category = 'General'

    def traits_view(self):
        v = View(remote_status_item('LabBook Repo'))

        return v

# ============= EOF =============================================



