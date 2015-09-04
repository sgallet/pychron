# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Str
from traitsui.api import Item

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.entry.entry_views.entry import BaseEntry


class ProjectEntry(BaseEntry):
    project = Str

    def _add_item(self):
        name = self.project
        dvc = self.dvc
        self.info('Attempting to add Project="{}"'.format(name))
        if not dvc.get_project(name):
            self.info('added project={}'.format(name))
            if dvc.add_project(name):
                return True
        else:
            self.warning_dialog('{} already exists'.format(name))

    def traits_view(self):
        return self._new_view(Item('project'), title='Edit Project')

# ============= EOF =============================================
