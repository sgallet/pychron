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
from enable.enable_traits import Pointer

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D
from pychron.canvas.canvas2D.scene.primitives.rounded import RoundedRectangle


def snap_to_grid(dx, dy, interval):
    dx = round(dx / interval) * interval
    dy = round(dy / interval) * interval
    return dx, dy


class DesignerExtractionLineCanvas2D(ExtractionLineCanvas2D):
    drag_pointer = Pointer('bullseye')
    snap_to_grid = True
    grid_interval = 0.5
    _constrain = False

    _px = None
    _py = None
    selected_item = None

    def drag_mouse_move(self, event):
        si = self.selected_item

        x, y = event.x, event.y
        dx, dy = self.map_data((x, y))
        w, h = si.width, si.height

        dx -= w / 2.
        dy -= h / 2.

        if self.snap_to_grid:
            dx, dy = snap_to_grid(dx, dy, interval=self.grid_interval)

        if event.shift_down:
            if self._px is not None and not self._constrain:
                xx = abs(x - self._px)
                yy = abs(y - self._py)
                self._constrain = 'v' if yy > xx else 'h'
            else:
                self._px = x
                self._py = y
        else:
            self._constrain = False
            self._px, self._py = None, None

        if self._constrain == 'h':
            si.x = dx
        elif self._constrain == 'v':
            si.y = dy
        else:
            si.x, si.y = dx, dy

    def drag_left_up(self, event):
        self._set_normal_state(event)

    def drag_mouse_leave(self, event):
        self._set_normal_state(event)

    def _set_normal_state(self, event):
        self.event_state = 'normal'
        event.window.set_pointer(self.normal_pointer)

    def select_left_down(self, event):
        self.event_state = 'drag'
        event.window.set_pointer(self.drag_pointer)

    def _over_item(self, event):
        x, y = event.x, event.y
        return next((item for item in self.scene.iteritems(klass=RoundedRectangle)
                     if hasattr(item, 'is_in') and \
                     item.is_in(x, y)), None)

    def normal_mouse_move(self, event):
        item = self._over_item(event)
        if item is not None:
            event.window.set_pointer(self.select_pointer)
            self.event_state = 'select'
            self.selected_item = item
        else:
            event.window.set_pointer(self.normal_pointer)
            self.selected_item = None

# ============= EOF =============================================
