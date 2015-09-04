# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup, TextEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================


class TipView(HasTraits):
    text = Str
    message = Str('<h1><font color=orange>Did you know?</font></h1>')

    def traits_view(self):
        v = View(UItem('message', style='readonly'),
                 UItem('text',
                       style='custom',
                       editor=TextEditor(read_only=True)),
                 buttons=['OK'],
                 height=400,
                 width=400,
                 title='Random Tip',
                 kind='livemodal')
        return v


if __name__ == '__main__':
    t = TipView()
    t.configure_traits()
# ============= EOF =============================================



