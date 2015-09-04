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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Instance
from traitsui.api import Spring, View, UItem

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.displays.display import DisplayController


def spacer(width=-1, **kw):
    return Spring(springy=False, width=width, **kw)


class ConsolePane(TraitsDockPane):
    id = 'pychron.console'
    name = 'Console'
    console_display = Instance(DisplayController)

    def traits_view(self):
        v = View(UItem('console_display',
                       style='custom'))
        return v

# ============= EOF =============================================

