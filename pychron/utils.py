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
from collections import namedtuple

def get_display_size():
    size = namedtuple('Size', 'width height')
    # if IsQt():
#        from PySide.QtGui import QDesktopWidget
    from PySide.QtGui import QApplication
    desktop = QApplication.desktop()
    rect = desktop.screenGeometry()
    w, h = rect.width(), rect.height()
#     else:
#         import wx
#         rect = wx.GetDisplaySize()
#         w, h = rect.width, rect.height
#
    return size(w, h)
#
# def IsQt():
#     from traits.etsconfig.api import ETSConfig
#     return ETSConfig.toolkit == "qt4"
