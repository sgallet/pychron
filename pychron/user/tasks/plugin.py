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
from envisage.ui.tasks.task_factory import TaskFactory
from traits.api import HasTraits, Button
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.user.tasks.task import UsersTask


class UsersPlugin(BaseTaskPlugin):
    name = 'Users'
    id = 'pychron.users.plugin'

    def _tasks_default(self):
        return [TaskFactory(id='pychron.users',
                            factory=self._users_task_factory,
                            name='Users',
                            accelerator='Ctrl+Shift+U',
                            )]

    def _users_task_factory(self):
        t = UsersTask()
        return t

# ============= EOF =============================================



