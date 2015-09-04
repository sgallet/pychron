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
from traits.api import Bool, Str
from traitsui.api import View, Item, VGroup
from envisage.ui.tasks.preferences_pane import PreferencesPane

from pychron.envisage.tasks.base_preferences_helper import GitRepoPreferencesHelper, \
    remote_status_item

# from pychron.pychron_constants import PLUSMINUS
# ============= standard library imports ========================
# ============= local library imports  ==========================


class PyScriptPreferences(GitRepoPreferencesHelper):
    name = 'Scripts'
    preferences_path = 'pychron.pyscript'
    auto_detab = Bool
    use_git_repo = Bool
    use_name_prefix = Bool
    name_prefix = Str


class PyScriptPreferencesPane(PreferencesPane):
    category = 'Scripts'
    model_factory = PyScriptPreferences

    def traits_view(self):
        prefix_grp = VGroup(Item('use_name_prefix'),
                            Item('name_prefix', enabled_when='use_name_prefix'),
                            show_border=True, label='Prefix')

        git_grp = VGroup(Item('use_git_repo'),
                         remote_status_item('Script Repo'),
                         show_border=True, label='Git')
        v = View(VGroup(Item('auto_detab'),
                        prefix_grp, git_grp))

        return v

        # ============= EOF =============================================
