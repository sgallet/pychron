# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import Any
from chaco.api import AbstractOverlay
# ============= standard library imports ========================

# ============= local library imports  ==========================
# from pychron.image.video import Video

class VideoUnderlay(AbstractOverlay):
    """
        video only needs to be an object the implements
        get_image_data([,size=(w,h)])
            returns  ndarray
    """
    video = Any

    def overlay(self, component, gc, *args, **kw):
        """

        """
        with gc:
            gc.clip_to_rect(self.component.x, self.component.y,
                            self.component.width, self.component.height)
            gc.translate_ctm(self.component.x, self.component.y)

            if self.video:
                img = self.video.get_image_data(
                                                size=(component.width,
                                                      component.height)
                                                )
                if img is not None:
                    gc.draw_image(img)

# ============= EOF ====================================
