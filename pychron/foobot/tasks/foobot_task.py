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
from pyface.tasks.task_layout import TaskLayout
from traits.api import Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task import BaseTask
from pychron.foobot.foobot import Foobot
from pychron.foobot.tasks.panes import FoobotPane


class FoobotTask(BaseTask):
    name = 'Foobot'
    bot = Instance(Foobot)

    def create_central_pane(self):
        return FoobotPane(model=self.bot)

    def _bot_default(self):
        return Foobot(application=self.application)

    def _default_layout_default(self):
        return TaskLayout()
# ============= EOF =============================================



