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
from traits.api import Property
from traitsui.api import View, UItem, Group, InstanceEditor, HGroup, \
    EnumEditor, Item, spring, Spring, ButtonEditor, VGroup, RangeEditor
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.experiment.utilities.identifier import pretty_extract_device
from pychron.core.ui.led_editor import LEDEditor
from enable.component_editor import ComponentEditor


# def SUItem(name, **kw):
#     return UItem('object.stage_manager.{}'.format(name), **kw)


class BaseLaserPane(TraitsTaskPane):
    def trait_context(self):
        return {'object': self.model.stage_manager}

    def traits_view(self):
        editor = self.model.stage_manager.canvas_editor_factory()
        canvas_grp = VGroup(
            HGroup(UItem('stage_map_name', editor=EnumEditor(name='stage_map_names')),
                   Item('stage_map',
                        show_label=False),
                   Item('back_button',
                        enabled_when='linear_move_history',
                        show_label=False),
                   spring),
            UItem('canvas', style='custom', editor=editor))

        return View(canvas_grp)
        # v = View(UItem('stage_manager',
        #                style='custom'),
        #          HGroup(UItem('status_text', style='readonly'), spring))
        # return v


class AxesPane(TraitsDockPane):
    name = 'Axes'

    def traits_view(self):
        agrp = UItem('stage_controller', style='custom')
        return View(agrp)


class StageControlPane(TraitsDockPane):
    name = 'Stage'

    def trait_context(self):
        return {'canvas': self.model.stage_manager.canvas,
                'stage_manager': self.model.stage_manager,
                'tray_calibration': self.model.stage_manager.tray_calibration_manager}

    def traits_view(self):
        # =======================================================================
        # convienience functions
        # =======================================================================
        # def make_sm_name(name):
        #     return 'object.stage_manager.{}'.format(name)

        # def SItem(name, **kw):
        #     return Item(make_sm_name(name), **kw)

        # def CItem(name, **kw):
        #     return Item('object.stage_manager.canvas.{}'.format(name), **kw)
        #
        # def CUItem(name, **kw):
        #     return UItem('object.stage_manager.canvas.{}'.format(name), **kw)

        pgrp = Group(UItem('stage_manager.calibrated_position_entry',
                           tooltip='Enter a positon e.g 1 for a hole, or 3,4 for X,Y'),
                     label='Calibrated Position',
                     show_border=True)
        hgrp = HGroup(UItem('stage_manager.stop_button'),
                      UItem('stage_manager.home'),
                      UItem('stage_manager.home_option',
                            editor=EnumEditor(name='stage_manager.home_options')))

        cngrp = VGroup(Item('canvas.show_bounds_rect'),
                       Item('canvas.show_grids'),
                       HGroup(Item('canvas.show_laser_position'),
                              UItem('canvas.crosshairs_color')),
                       Item('canvas.crosshairs_kind'),
                       Item('canvas.crosshairs_radius'),
                       HGroup(
                           Item('canvas.crosshairs_offsetx', label='Offset'),
                           UItem('canvas.crosshairs_offsety')),
                       Item('canvas.crosshairs_offset_color'),
                       HGroup(Item('canvas.show_desired_position'),
                              UItem('canvas.desired_position_color')),
                       label='Canvas')

        mode = self.model.mode
        cagrp = VGroup(
            visible_when='use_video',
            label='Camera')

        if self.model.stage_manager.__class__.__name__ == 'VideoStageManager':
            mvgrp = VGroup(
                UItem('stage_manager.autocenter_manager', style='custom'),
                UItem('stage_manager.autofocus_manager', style='custom'),
                label='Machine Vision', show_border=True)

            recgrp = VGroup(
                HGroup(icon_button_editor('stage_manager.snapshot_button', 'camera',
                                          tooltip='Take a snapshot'),
                       icon_button_editor('stage_manager.record',
                                          'media-record',
                                          tooltip='Record video'),
                       CustomLabel('stage_manager.record_label', color='red')),
                VGroup(Item('stage_manager.auto_save_snapshot'),
                       Item('stage_manager.render_with_markup')),
                show_border=True,
                label='Recording')

            cfggrp = VGroup(Item('stage_manager.camera_zoom_coefficients', label='Zoom Coefficients'))
            cagrp.content.extend((cfggrp, recgrp, mvgrp))

        cgrp = Group(
            UItem('stage_manager.stage_controller', style='custom',
                  label='Axes'),
            cngrp,
            cagrp,
            layout='tabbed')

        if mode != 'client':
            pp_grp = UItem('stage_manager.points_programmer',
                           label='Points',
                           style='custom')
            cgrp.content.append(pp_grp)

            tc_grp = VGroup(UItem('tray_calibration.style',
                                  enabled_when='not tray_calibration.isCalibrating()'),
                            UItem('tray_calibration.calibrate',
                                  editor=ButtonEditor(label_value='tray_calibration.calibration_step')),
                            HGroup(Item('tray_calibration.x', format_str='%0.3f', style='readonly'),
                                   Item('tray_calibration.y', format_str='%0.3f', style='readonly')),
                            Item('tray_calibration.rotation', format_str='%0.3f', style='readonly'),
                            Item('tray_calibration.scale', format_str='%0.4f', style='readonly'),
                            Item('tray_calibration.error', format_str='%0.2f', style='readonly'),
                            UItem('tray_calibration.calibrator', style='custom', editor=InstanceEditor()),
                            CustomLabel('tray_calibration.calibration_help',
                                        color='green',
                                        height=75, width=300),
                            label='Calibration')

            cgrp.content.append(tc_grp)

        v = View(VGroup(hgrp, pgrp, cgrp))

        return v


class ControlPane(TraitsDockPane):
    name = 'Control'

    movable = False
    closable = False
    floatable = False

    def traits_view(self):
        v = View(
            VGroup(
                HGroup(
                    UItem('enabled_led',
                          editor=LEDEditor(),
                          style='custom',
                          height=-35),
                    UItem('enable', editor=ButtonEditor(label_value='enable_label'))),
                HGroup(
                    Item('requested_power',
                         style='readonly',
                         format_str='%0.2f',
                         width=100),
                    Spring(springy=False, width=50),
                    UItem('units', style='readonly'),
                    spring),
                show_border=True))
        return v


class SupplementalPane(TraitsDockPane):
    pass


# ===============================================================================
# generic
# ===============================================================================
class PulsePane(TraitsDockPane):
    id = 'pychron.lasers.pulse'
    name = 'Pulse'

    def traits_view(self):
        v = View(Group(UItem('pulse', style='custom'), show_border=True))
        return v


class OpticsPane(TraitsDockPane):
    id = 'pychron.lasers.optics'
    name = 'Optics'

    def traits_view(self):
        v = View(Group(UItem('laser_controller',
                             editor=InstanceEditor(view='control_view'),
                             style='custom'),
                       show_border=True))
        return v


class ClientMixin(object):
    name = Property(depends_on='model')
    id = 'pychron.lasers.client'

    def _get_name(self):
        n = 'Laser Client'
        if self.model:
            n = pretty_extract_device(self.model.name)
        return n

    def traits_view(self):
        pos_grp = VGroup(HGroup(Item('position'), Item('use_autocenter', label='Autocenter')),
                         Item('x', editor=RangeEditor(low=-25.0, high=25.0)),
                         Item('y', editor=RangeEditor(low=-25.0, high=25.0)),
                         Item('z', editor=RangeEditor(low=-25.0, high=25.0)),
                         label='Positioning')

        ogrp = Group(UItem('optics_client', style='custom'),
                     label='Optics')
        cgrp = Group(UItem('controls_client', style='custom'),
                     defined_when='controls_client',
                     label='Controls')

        tgrp = Group(cgrp,
                     ogrp,
                     pos_grp, layout='tabbed')

        egrp = HGroup(UItem('enabled_led', editor=LEDEditor()),
                      UItem('enable', editor=ButtonEditor(label_value='enable_label')),
                      spring,
                      icon_button_editor('snapshot_button', 'camera'),
                      icon_button_editor('test_connection_button',
                                         'connect', tooltip='Test Connection'))
        v = View(VGroup(egrp, tgrp))
        return v


class ClientPane(TraitsTaskPane, ClientMixin):
    pass
    # def traits_view(self):
    #     v = View(
    #         Item('test_connection_button', show_label=False),
    #         HGroup(
    #             UItem('enabled_led', editor=LEDEditor()),
    #             UItem('enable', editor=ButtonEditor(label_value='enable_label'))),
    #         Item('position'),
    #         UItem('snapshot_button'),
    #         Item('x', editor=RangeEditor(low=-25.0, high=25.0)),
    #         Item('y', editor=RangeEditor(low=-25.0, high=25.0)),
    #         Item('z', editor=RangeEditor(low=-25.0, high=25.0)))
    #     return v


class ClientDockPane(TraitsDockPane, ClientMixin):
    pass


class AuxilaryGraphPane(TraitsDockPane):
    name = 'Auxilary Graph'

    def traits_view(self):
        v = View(UItem('auxilary_graph', editor=ComponentEditor()))
        return v

# from pyface.tasks.enaml_dock_pane import EnamlDockPane
# import enaml
# class TestPane(EnamlDockPane):
#    model = Any
#    def create_component(self):
#        with enaml.imports():
#            from test_view import TestView
#
#        view = TestView(model=self.model)
#        return view
# FusionsDiodePane = BaseLaserPane

# FusionsDiodeControlPane = ControlPane
# ============= EOF =============================================
