# ===============================================================================
# Copyright 2011 Jake Ross
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
from PySide import QtCore
from PySide.QtGui import QWidget, QImage, QPixmap
from pyface.qt import QtGui
from traits.has_traits import HasTraits
from traits.trait_types import Str
from traitsui.item import UItem
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor
from traitsui.view import View
from pychron.image.cv_wrapper import get_capture_device


class VideoWidget(QWidget):
    def __init__(self):
        super(VideoWidget, self).__init__()
        hbox = QtGui.QHBoxLayout(self)

        lbl = QtGui.QLabel(self)
        self.label = lbl
        self.cap = get_capture_device()
        self.cap.open(0)
        # lbl.setPixmap(image.create_image())
        self.set_frame()
        hbox.addWidget(lbl)
        self.setLayout(hbox)
        self.startTimer(100)

    def timerEvent(self, *args, **kwargs):
        self.set_frame()

    def set_frame(self):
        ok, data = self.cap.read()
        shape = data.shape
        im = QImage(data, shape[1], shape[0], QImage.Format_RGB888)
        pix = QPixmap.fromImage(QImage.rgbSwapped(im))
        self.label.setPixmap(pix)


class _VideoEditor(Editor):
    def init(self, parent):
        self.control = self._create_control()

        # anim = QtCore.QPropertyAnimation(self.control, "count")
        #
        # anim.setDuration(1000)
        # anim.setStartValue(1)
        # anim.setEndValue(32)
        # anim.setLoopCount(-1)
        # # anim.setEasingCurve(QtCore.QEasingCurve.InOutBack)
        # QtCore.QObject.connect(anim, QtCore.SIGNAL("finished()"), anim, QtCore.SLOT("deleteLater()"))
        # anim.start()
        #
        # self._animation = anim
        # # QtCore.QTimer.singleShot(100, anim, QtCore.SLOT("start()"))

    def _create_control(self):
        v = VideoWidget()
        return v

    def update_editor(self):
        pass


class VideoEditor(BasicEditorFactory):
    klass = _VideoEditor


class Demo(HasTraits):
    a = Str('aa')
    # state = Button

    def traits_view(self):
        v = View(UItem('a', editor=VideoEditor()),
                 # UItem('state'),
                 width=1200,
                 height=700)
        return v


d = Demo()
d.configure_traits()
# # ============= enthought library imports =======================
# from traits.api import DelegatesTo, Instance
# from traitsui.api import View, Item, HGroup, spring
#
# # ============= standard library imports ========================
# import sys
# import os
# # ============= local library imports  ==========================
# # add pychron to the path
# root = os.path.basename(os.path.dirname(__file__))
# if 'pychron_beta' not in root:
# root = 'pychron_beta'
# src = os.path.join(os.path.expanduser('~'),
#                    'Programming',
#                    root
# )
# sys.path.append(src)
#
# from pychron.lasers.stage_managers.video_component_editor import VideoComponentEditor
# from pychron.managers.videoable import Videoable
# from pychron.canvas.canvas2D.video_laser_tray_canvas import VideoLaserTrayCanvas
#
#
# class VideoDisplayCanvas(VideoLaserTrayCanvas):
#     show_grids = False
#     show_axes = False
#     use_camera = False
#
#
# class VideoPlayer(Videoable):
#     canvas = Instance(VideoDisplayCanvas)
#     crosshairs_kind = DelegatesTo('canvas')
#     crosshairs_color = DelegatesTo('canvas')
#
#     def _canvas_default(self):
#         self.video.open(user='underlay')
#         return VideoDisplayCanvas(padding=30,
#                                   video=self.video_manager.video)
#
#     def traits_view(self):
#         vc = Item('canvas',
#                   style='custom',
#                   editor=VideoComponentEditor(width=640, height=480),
#                   show_label=False,
#                   resizable=False,
#
#         )
#         v = View(
#
#             HGroup(spring, Item('crosshairs_kind'), Item('crosshairs_color')),
#             vc,
#             #                 width = 800,
#             height=530,
#             title='Video Display'
#         )
#         return v
#
#
# if __name__ == '__main__':
#     v = VideoPlayer()
#     v.configure_traits()
# ============= EOF ====================================
