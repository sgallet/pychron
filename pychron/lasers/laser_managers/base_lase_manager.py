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
import time
from traits.api import Instance, Event, Bool, Any, Property, Str, Float, provides
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.strtools import to_bool
from pychron.core.ui.gui import wake_screen
from pychron.lasers.stage_managers.stage_manager import StageManager
from pychron.lasers.pattern.pattern_executor import PatternExecutor
from pychron.managers.manager import Manager
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.core.ui.led_editor import LED
from pychron.core.helpers.filetools import list_directory
from pychron.paths import paths


@provides(ILaserManager)
class BaseLaserManager(Manager):
    # implements(ILaserManager)
    # provides(ILaserManager)
    pattern_executor = Instance(PatternExecutor)
    use_video = Bool(False)

    enable = Event
    enable_label = Property(depends_on='enabled')
    enabled_led = Instance(LED, ())
    enabled = Bool(False)

    stage_manager = Instance(StageManager)

    requested_power = Any
    status_text = Str
    pulse = Any
    laser_controller = Any
    mode = 'normal'

    use_calibrated_power = Bool(True)
    requested_power = Property(Float, depends_on='_requested_power')
    units = Property(depends_on='use_calibrated_power')
    _requested_power = Float
    _calibrated_power = None
    _cancel_blocking = False

    def test_connection(self):
        if self.mode == 'client':
            return self._test_connection()
        else:
            return True

    def initialize_video(self):
        if self.use_video:
            self.stage_manager.initialize_video()

    def update_position(self):
        self.debug('update position')
        pos = self.get_position()
        self.debug('got position {}'.format(pos))
        if pos:
            self.stage_manager.trait_set(**dict(zip(('_x_position', '_y_position', '_z_position'), pos)))
            return True

    def wake(self):
        wake_screen()

    def is_ready(self):
        return True

    def take_snapshot(self, *args, **kw):
        pass

    def end_extract(self, *args, **kw):
        pass

    def extract(self, *args, **kw):
        pass

    def prepare(self, *args, **kw):
        pass

    def get_motor_lock(self, name, value):
        pass

    def set_motor(self, *args, **kw):
        pass

    def get_motor(self, name):
        pass

    def get_response_blob(self):
        return ''

    def get_output_blob(self):
        return ''

    def enable_device(self, **kw):
        return self.enable_laser(**kw)

    def disable_device(self):
        self.disable_laser()

    def enable_laser(self, **kw):
        pass

    def disable_laser(self):
        pass

    def get_pattern_names(self):
        p = paths.pattern_dir
        extension = '.lp,.txt'
        patterns = list_directory(p, extension)
        return ['', ] + patterns

#     def new_pattern_maker(self):
#         pm = PatternMakerView()
#         self.open_view(pm)
#
#     def open_pattern_maker(self):
#         pm = PatternMakerView(
#                               executor=self.pattern_executor
#                               )
#         if pm.load_pattern():
#             self.open_view(pm)

    def execute_pattern(self, name=None, block=False):
        if not self.stage_manager.temp_hole:
            self.information_dialog('Need to specify a hole')
            return

        pm = self.pattern_executor
        if pm.load_pattern(name):
            pm.set_stage_values(self.stage_manager)
            pm.execute(block)

    def get_brightness(self):
        return 0

    def stop_pattern(self):
        if self.pattern_executor:
            self.pattern_executor.stop()

    def isPatterning(self):
        if self.pattern_executor:
            return self.pattern_executor.isPatterning()

    def _pattern_executor_default(self):
        controller = None
        if hasattr(self, 'stage_manager'):
            controller = self.stage_manager.stage_controller

        pm = PatternExecutor(application=self.application,
                             controller=controller,
                             laser_manager=self)
        return pm

    def move_to_position(self, pos, *args, **kw):
        if not isinstance(pos, list):
            pos = [pos]

        for p in pos:
            self._move_to_position(p, *args, **kw)

        return True

    def trace_path(self, *args, **kw):
        pass

    def drill_point(self, *args, **kw):
        pass

    def set_motors_for_point(self, pt):
        pass

    def get_achieved_output(self):
        pass

    # private
    def _move_to_position(self, *args, **kw):
        pass

    def _block(self, cmd='GetDriveMoving', cmpfunc=None, period=0.25, position_callback=None):

        ask = self._ask

        cnt = 0
        tries = 0
        maxtries = int(500 / float(period))  # timeout after 50 s
        nsuccess = 2
        self._cancel_blocking = False
        if cmpfunc is None:
            cmpfunc = to_bool

        while tries < maxtries and cnt < nsuccess:
            if self._cancel_blocking:
                break

            time.sleep(period)
            resp = ask(cmd)

            if self.communicator.simulation:
                resp = 'False'

            if resp is not None:
                try:
                    if not cmpfunc(resp):
                    # if not to_bool(resp):
                        cnt += 1
                except (ValueError, TypeError):
                    cnt = 0

                if position_callback:
                    if self.communicator.simulation:
                        x, y, z = cnt / 3., cnt / 3., 0
                        position_callback(x, y, z)
                    else:
                        xyz = self.get_position()
                        if xyz:
                            position_callback(*xyz)
            else:
                cnt = 0
            tries += 1

        state = cnt >= nsuccess
        if state:
            self.info('Block completed')
        else:
            if self._cancel_blocking:
                self.info('Block failed. canceled by user')
            else:
                self.warning('Block failed. timeout after {}s'.format(maxtries * period))

        return state

    # ===============================================================================
    # getter/setters
    # ===============================================================================
    def _get_enable_label(self):
        """
        """
        return 'DISABLE' if self.enabled else 'ENABLE'

    def _get_calibrated_power(self, power, use_calibration=True, verbose=True):
        if power:
            if self.use_calibrated_power and use_calibration:
                power = max(0, self.laser_controller.get_calibrated_power(power, verbose=verbose))
        return power

    def _get_requested_power(self):
        return self._requested_power

    def _get_units(self):
        return '(W)' if self.use_calibrated_power else '(%)'

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _enabled_changed(self):
        if self.enabled:
            self.enabled_led.state = 'green'
        else:
            self.enabled_led.state = 'red'

    def _use_video_changed(self):
        if not self.use_video:
            try:
                self.stage_manager.video.close()
            except AttributeError, e:
                print 'use video 1', e

        try:
            sm = self._stage_manager_factory(self.stage_args)

            sm.stage_controller = self.stage_manager.stage_controller
            sm.stage_controller.parent = sm
            if self.plugin_id:
                sm.bind_preferences(self.plugin_id)
#             sm.visualizer = self.stage_manager.visualizer

            sm.load()

            self.stage_manager = sm
        except AttributeError, e:
            print 'use video 2', e

    def _stage_manager_factory(self, args):
        self.stage_args = args
        if self.use_video:
            from pychron.lasers.stage_managers.video_stage_manager import VideoStageManager
            klass = VideoStageManager
        else:
            klass = StageManager

        args['parent'] = self
        sm = klass(**args)
        sm.id = self.stage_manager_id
        return sm
# ============= EOF =============================================
