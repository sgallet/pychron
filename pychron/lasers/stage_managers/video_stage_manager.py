#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Instance, String, Property, Button, \
    Bool, Event, on_trait_change, Str, Int
# from traitsui.api import Group, Item, HGroup, VGroup
# from pyface.timer.api import do_later
from apptools.preferences.preference_binding import bind_preference
from chaco.plot_graphics_context import PlotGraphicsContext
#============= standard library imports ========================
import time
from threading import Thread, Timer

import os
#============= local library imports  ==========================
from pychron.helpers.filetools import unique_path
from pychron.paths import paths
# from pychron.machine_vision.autofocus_manager import AutofocusManager
from pychron.helpers.archiver import Archiver
from pychron.image.video_server import VideoServer
from pychron.image.video import Video
from pychron.canvas.canvas2D.camera import Camera
# from pychron.machine_vision.autocenter_manager import AutocenterManager
# from pychron.machine_vision.mosaic_manager import MosaicManager

# from camera_calibration_manager import CameraCalibrationManager
from stage_manager import StageManager
# from video_component_editor import VideoComponentEditor
# from pychron.helpers.media import play_sound
# from pychron.mv.autocenter_manager import AutoCenterManager
# from pychron.mv.focus.autofocus_manager import AutoFocusManager
from pychron.ui.stage_component_editor import VideoComponentEditor
# from pychron.ui.gui import invoke_in_main_thread

try:
    from pychron.canvas.canvas2D.video_laser_tray_canvas import VideoLaserTrayCanvas
except ImportError:
    from pychron.canvas.canvas2D.laser_tray_canvas import LaserTrayCanvas as VideoLaserTrayCanvas

# from calibration_manager import CalibrationManager
class VideoStageManager(StageManager):
    '''
    '''
    video = Instance(Video)
    canvas_editor_klass = VideoComponentEditor
    #    calibration_manager = Instance(CalibrationManager)
    #     camera_xcoefficients = Property(String(enter_set=True, auto_set=False),
    #                                    depends_on='_camera_xcoefficients')
    #     _camera_xcoefficients = String
    #
    #     camera_ycoefficients = Property(String(enter_set=True, auto_set=False),
    #                                    depends_on='_camera_ycoefficients')
    #     _camera_ycoefficients = String

    camera_zoom_coefficients = Property(String(enter_set=True, auto_set=False),
                                        depends_on='_camera_zoom_coefficients')
    _camera_zoom_coefficients = String

    #     camera_calibration_manager = Instance(CameraCalibrationManager)
    #     calculate = Button

    #     calibrate_focus = Button
    #     focus_z = Float

    #     calculate_offsets = Bool

    #     pxpercmx = DelegatesTo('camera_calibration_manager')
    #     pxpercmy = DelegatesTo('camera_calibration_manager')

    use_auto_center_interpolation = Bool(False)

    autocenter_button = Button('AutoCenter')
    configure_autocenter_button = Button('Configure')

    #    mosaic_manager = Instance(MosaicManager)
    #     autofocus_manager = Instance(AutoFocusManager)
    #     autocenter_manager = Instance(AutoCenterManager)
    #     # from pychron.mv.autocenter_manager import AutoCenterManager
    # from pychron.mv.focus.autofocus_manager import AutoFocusManager
    autocenter_manager = Instance('pychron.mv.autocenter_manager.AutoCenterManager')
    autofocus_manager = Instance('pychron.mv.focus.autofocus_manager.AutoFocusManager')
    snapshot_button = Button('Snapshot')
    auto_save_snapshot = Bool(True)

    record = Event
    record_label = Property(depends_on='is_recording')
    is_recording = Bool

    use_db = False

    use_video_archiver = Bool(True)
    video_archiver = Instance(Archiver)
    video_identifier = Str
    #     video_identifier = Enum(1, 2)
    use_video_server = Bool(False)
    video_server_port = Int
    video_server_quality = Int
    video_server = Instance(VideoServer)

    use_media_server = Bool(False)
    auto_upload = Bool(False)

    camera = Instance(Camera)

    render_with_markup = Bool(False)

    _auto_correcting = False

    def bind_preferences(self, pref_id):
        self.debug('binding preferences')
        super(VideoStageManager, self).bind_preferences(pref_id)

        bind_preference(self.autocenter_manager, 'use_autocenter', '{}.use_autocenter'.format(pref_id))
        bind_preference(self, 'render_with_markup', '{}.render_with_markup'.format(pref_id))
        bind_preference(self, 'auto_upload', 'pychron.media_server.auto_upload')
        bind_preference(self, 'use_media_server', 'pychron.media_server.use_media_server')
        #        bind_preference(self.pattern_manager,
        #                        'record_patterning',
        #                         '{}.record_patterning'.format(pref_id))
        #
        #        bind_preference(self.pattern_manager,
        #                         'show_patterning',
        #                         '{}.show_patterning'.format(pref_id))

        bind_preference(self, 'use_video_archiver',
                        '{}.use_video_archiver'.format(pref_id)
        )

        bind_preference(self, 'video_identifier',
                        '{}.video_identifier'.format(pref_id)
        )

        bind_preference(self, 'use_video_server',
                        '{}.use_video_server'.format(pref_id)
        )
        if self.use_video_server:
            bind_preference(self.video_server, 'port',
                            '{}.video_server_port'.format(pref_id)
            )
            bind_preference(self.video_server, 'quality',
                            '{}.video_server_quality'.format(pref_id)
            )

        bind_preference(self.video_archiver, 'archive_months',
                        '{}.video_archive_months'.format(pref_id)
        )
        bind_preference(self.video_archiver, 'archive_days',
                        '{}.video_archive_days'.format(pref_id)
        )
        bind_preference(self.video_archiver, 'archive_hours',
                        '{}.video_archive_hours'.format(pref_id)
        )
        bind_preference(self.video_archiver, 'root',
                        '{}.video_directory'.format(pref_id)
        )

        bind_preference(self.video, 'output_mode', '{}.video_output_mode'.format(pref_id))
        bind_preference(self.video, 'ffmpeg_path', '{}.ffmpeg_path'.format(pref_id))


    def start_recording(self, new_thread=True, **kw):
        '''
        '''
        if new_thread:
            t = Thread(target=self._start_recording, kwargs=kw)
            t.start()
        else:
            self._start_recording(**kw)
        self.is_recording = True

    def stop_recording(self, user='remote', delay=None):
        '''
        '''

        def close():
            self.is_recording = False
            self.info('stop video recording')

            if self.video.stop_recording(wait=True):
                self._upload(self.video.output_path)


                # clean the video directory
            #             self.clean_video_archive()

        if self.video._recording:
            if delay:
                t = Timer(delay, close)
                t.start()
            else:
                close()

            #    def update_camera_params(self, obj, name, old, new):
            #        if name == 'focus_z':
            #            self.focus_z = new
            #        elif 'y' in name:
            #            self._camera_ycoefficients = new
            #        elif 'x' in name:
            #            self._camera_xcoefficients = new

            #    def finish_loading(self):
            #        super(VideoStageManager, self).finish_loading()
            #        if self.use_video_server:
            #            self.video_server.start()

    def initialize_video(self):
        if self.video:
            self.video.open(
                identifier=self.video_identifier
            )


    def initialize_stage(self):
        super(VideoStageManager, self).initialize_stage()
        self.initialize_video()

        s = self.stage_controller
        if s.axes:
            xa = s.axes['x'].drive_ratio
            ya = s.axes['y'].drive_ratio

            self._drive_xratio = xa
            self._drive_yratio = ya

        self._update_zoom(0)

    #        from pychron.helpers.media import load_sound, play_sound
    #        load_sound('shutter')
    #        play_sound('shutter')
    def autocenter(self, *args, **kw):
        return self._autocenter(*args, **kw)

    def snapshot(self, path=None, name=None, auto=False, inform=True):
        '''
            path: abs path to use
            name: base name to use if auto saving in default dir
            auto: force auto save

            returns:
                    path: local abs path
                    upath: remote abs path
        '''

        if path is None:
            if self.auto_save_snapshot or auto:

                if name is None:
                    name = 'snapshot'
                path, _cnt = unique_path(root=paths.snapshot_dir, base=name,
                                         extension='jpg')
            else:
                path = self.save_file_dialog()

        if path:
            self.info('saving snapshot {}'.format(path))
            #            from pychron.helpers.media import play_sound

            # play camera shutter sound
            #             play_sound('shutter')

            self._render_snapshot(path)
            #            if self.render_with_markup:
            #                self._render_with_markup(path)
            #            else:
            #                self.video.record_frame(path, swap_rb=False)
            upath = self._upload(path)
            if inform:
                self.information_dialog('Snapshot save to {}. Uploaded to'.format(path, upath))

            return path, upath

    def kill(self):
        '''
        '''

        super(VideoStageManager, self).kill()
        if self.camera:
            self.camera.save_calibration()

        self.canvas.close_video()
        if self.video:
            self.video.close(force=True)

        #        if self.use_video_server:
        #            self.video_server.stop()
        if self._stage_maps:
            for s in self._stage_maps:
                s.dump_correction_file()

        self.clean_video_archive()

    def clean_video_archive(self):
        if self.use_video_archiver:
            self.info('Cleaning video directory')

            self.video_archiver.clean(spawn_process=False)

    def _upload(self, path):
        if self.use_media_server and self.auto_upload:
            client = self.application.get_service('pychron.media_server.client.MediaClient')
            if client is not None:
                url = client.url()
                self.info('uploading {} to {}'.format(path, url))
                if not client.upload(path, dest='images/{}'.format(self.parent.name)):
                    self.warning('failed to upload {} to media server at {}'.format(path, url))
                    self.warning_dialog('Failed to Upload {}. Media Server at {} unavailable'.format(path, url))
                else:
                    return path

            else:
                self.warning('Media client unavailable')
                self.warning_dialog('Media client unavailable')

    def _render_snapshot(self, path):
        c = self.canvas
        p = None
        was_visible = False
        if not self.render_with_markup:
            p = c.show_laser_position
            c.show_laser_position = False
            if self.points_programmer.is_visible:
                c.hide_all()
                was_visible = True

        gc = PlotGraphicsContext((int(c.outer_width), int(c.outer_height)))
        c.do_layout()
        gc.render_component(c)
        gc.save(path)

        if p is not None:
            c.show_laser_position = p

        if was_visible:
            c.show_all()
        #            self.points_programmer._show_hide_fired()


    def _start_recording(self, path=None, basename='vm_recording',
                         use_dialog=False, user='remote', ):
        if path is None:
            if use_dialog:
                path = self.save_file_dialog()
            else:
                vd = self.video_archiver.root
                self.debug('video archiver root {}'.format(vd))
                if vd is None:
                    vd = paths.video_dir
                path, _ = unique_path(vd, basename, extension='avi')

        self.info('start video recording {}'.format(path))
        d = os.path.dirname(path)
        if not os.path.isdir(d):
            self.warning('invalid directory {}'.format(d))
            self.warning('using default directory')
            path, _ = unique_path(paths.video_dir, basename,
                                  extension='avi')

        self.info('saving recording to path {}'.format(path))

        if self.use_db:
            db = self.get_video_database()
            db.connect()

            v = db.add_video_record(rid=basename)
            db.add_path(v, path)
            self.info('saving {} to database'.format(basename))
            db.commit()

        renderer = None
        if self.render_with_markup:
            renderer = self._render_snapshot

        self.video.start_recording(path, renderer)

    def is_auto_correcting(self):
        return self._auto_correcting

    def _move_to_hole_hook(self, holenum, correct):
        if correct and self.use_autocenter:
            self._auto_correcting = True
            pos, corrected, interp = self._autocenter(holenum=holenum, ntries=1)
            self._auto_correcting = False

            self._update_visualizer(holenum, pos, interp)

    def _update_visualizer(self, holenum, pos, interp):
        if pos:
        #                # add an adjustment value to the stage map
        #                sm.set_hole_correction(holenum, *pos)
        #                sm.dump_correction_file()
        #
            f = 'interpolation' if interp else 'correction'
        else:
            f = 'uncorrected'
        #                pos = sm.get_hole(holenum).nominal_position

        func = getattr(self.visualizer, 'record_{}'.format(f))
        func(holenum, *pos)

    def _autocenter(self, holenum=None, ntries=1, save=False, use_interpolation=False):
        rpos = None
        interp = False
        sm = self._stage_map

        if self.autocenter_manager.use_autocenter:
            time.sleep(0.75)
            for _t in range(max(1, ntries)):
            # use machine vision to calculate positioning error
            #                rpos = self.autocenter_manager.locate_target(
                rpos = self.autocenter_manager.locate_center(
                    self.stage_controller.x,
                    self.stage_controller.y,
                    holenum,
                    dim=self._stage_map.g_dimension
                )

                if rpos:
                    self.linear_move(*rpos, block=True,
                                     use_calibration=False,
                                     update_hole=False
                    )
                    time.sleep(0.75)
                else:
                    self.snapshot(auto=True,
                                  name='pos_err_{}_{}-'.format(holenum, _t))
                    break

                #            if self.use_auto_center_interpolation and rpos is None:
            if use_interpolation and rpos is None:
                self.info('trying to get interpolated position')
                rpos = sm.get_interpolated_position(holenum)
                if rpos:
                    s = '{:0.3f},{:0.3f}'
                    #                    self.visualizer.record_interpolation(holenum, *rpos)
                    interp = True
                else:
                    s = 'None'
                self.info('interpolated position= {}'.format(s))

        if rpos:
            corrected = True
            # add an adjustment value to the stage map
            if save:
                sm.set_hole_correction(holenum, *rpos)
                sm.dump_correction_file()
            #            f = 'interpolation' if interp else 'correction'
        else:
            corrected = False
            #            f = 'uncorrected'
            rpos = sm.get_hole(holenum).nominal_position

        return rpos, corrected, interp


    #===============================================================================
    # views
    #===============================================================================
    #===============================================================================
    # view groups
    #===============================================================================
    #    def _sconfig__group__(self):
    #        g = super(VideoStageManager, self)._sconfig__group__()
    #        mv = Group(HGroup(Item('use_autocenter', label='Enabled'),
    #                          Item('autocenter_button', show_label=False,
    #                               enabled_when='use_autocenter'),
    #                          Item('configure_autocenter_button', show_label=False),
    #                          ),
    #                   label='Machine Vision', show_border=True)
    #
    #        g.content.append(Group(Item('camera_xcoefficients'),
    #                               Item('camera_ycoefficients'),
    #                               # Item('drive_xratio'),
    #                               # Item('drive_yratio'),
    #                               mv,
    #                               VGroup(
    #                                     HGroup(Item('snapshot_button', show_label=False),
    #                                            VGroup(Item('auto_save_snapshot'),
    #                                             Item('render_with_markup'))),
    #                                     self._button_factory('record', 'record_label'),
    #                                     show_border=True,
    #                                     label='Recording'
    #                                     ),
    #                               Item('autofocus_manager', show_label=False, style='custom'),
    #                               # HGroup(Item('calculate', show_label=False), Item('calculate_offsets'), spring),
    # #                               Item('pxpercmx'),
    # #                               Item('pxpercmy'),
    # #                               HGroup(Item('calibrate_focus', show_label=False), Spring(width=20,
    # #                                                                                          springy=False),
    # #                                      Item('focus_z',
    # #                                            label='Focus',
    # #                                            style='readonly'
    # #                                            )),
    #                               label='Camera')
    #                         )
    #
    #        return g
    #===============================================================================
    # handlers
    #===============================================================================
    @on_trait_change('parent:motor_event')
    def _update_zoom(self, new):
        s = self.stage_controller
        if self.canvas.camera:
            if not isinstance(new, (int, float)):
                args, _ = new
                name, v = args[:2]
            else:
                name = 'zoom'
                v = new

            if name == 'zoom':
                pxpermm = self.canvas.camera.set_limits_by_zoom(v, s.x, s.y)
                self.pxpermm = pxpermm

    def _pxpermm_changed(self, new):
        if self.autocenter_manager:
            self.autocenter_manager.pxpermm = new

    def _autocenter_button_fired(self):
        self.autocenter()

    #     def _configure_autocenter_button_fired(self):
    #         info = self.autocenter_manager.edit_traits(view='configure_view',
    #                                                 kind='livemodal')
    #         if info.result:
    #             self.autocenter_manager.dump_detector()

    def _snapshot_button_fired(self):
        self.snapshot()

    def _record_fired(self):
    #            time.sleep(4)
    #            self.stop_recording()
        if self.is_recording:

            self.stop_recording()
        else:

            self.start_recording()

        #     def _calculate_fired(self):
        #         t = Thread(target=self._calculate_camera_parameters)
        #         t.start()
        #
        #     def _calibrate_focus_fired(self):
        #         z = self.stage_controller.z
        #         self.info('setting focus posiition {}'.format(z))
        #         self.canvas.camera.focus_z = z
        #         self.canvas.camera.save_focus()

    def _use_video_server_changed(self):
        if self.use_video_server:
            self.video_server.start()
        else:
            self.video_server.stop()

        #     def __stage_map_changed(self):
        #         self.visualizer.stage_map = self._stage_map
        #===============================================================================
        # property get/set
        #===============================================================================
        #     def _get_camera_xcoefficients(self):
        #         return self._camera_xcoefficients
        #
        #     def _set_camera_xcoefficients(self, v):
        #         self._camera_coefficients = v
        #         self.canvas.camera.calibration_data.xcoeff_str = v
        #         self._update_xy_limits()
        #
        #     def _get_camera_ycoefficients(self):
        #         return self._camera_ycoefficients
        #
        #     def _set_camera_ycoefficients(self, v):
        #         self._camera_ycoefficients = v
        #         self.canvas.camera.calibration_data.ycoeff_str = v
        #         self._update_xy_limits()

    def _get_camera_zoom_coefficients(self):
        return self.canvas.camera.zoom_coefficients

    def _set_camera_zoom_coefficients(self, v):
        print v
        self.canvas.camera.zoom_coefficients = ','.join(map(str, v))
        self._update_xy_limits()

    def _validate_camera_zoom_coefficients(self, v):
        try:
            return map(float, v.split(','))
        except ValueError:
            pass

    def _update_xy_limits(self):
        z = 0
        if self.parent is not None:
            zoom = self.parent.get_motor('zoom')
            if zoom is not None:
                z = zoom.data_position

        x = self.stage_controller.get_current_position('x')
        y = self.stage_controller.get_current_position('y')
        pxpermm = self.canvas.camera.set_limits_by_zoom(z, x, y)
        self.pxpermm = pxpermm

    def _get_record_label(self):
        return 'Record' if not self.is_recording else 'Stop'

    #===============================================================================
    # factories
    #===============================================================================
    def _canvas_factory(self):
        '''
        '''
        try:
            video = self.video
        except AttributeError:
            self.warning('Video not Available')
            video = None

        v = VideoLaserTrayCanvas(parent=self,
                                 padding=30,
                                 video=video,
                                 camera=self.camera,
                                 #                               use_camera=True,
                                 #                               map=self._stage_map
        )
        self.camera.parent = v
        return v

    #    def _canvas_editor_factory(self):
    #        camera = self.camera
    #        canvas = self.canvas
    #        if camera:
    #            w = camera.width * int(canvas.scaling * 10) / 10.
    #            h = camera.height * int(canvas.scaling * 10) / 10.
    #        else:
    #            w = 640
    #            h = 480
    #
    #        l = canvas.padding_left
    #        r = canvas.padding_right
    #        t = canvas.padding_top
    #        b = canvas.padding_bottom
    #        print w, h
    #        return self.canvas_editor_klass(width=w + l + r,
    #                                        height=h + t + b)
    #===============================================================================
    # defaults
    #===============================================================================
    def _camera_default(self):
        camera = Camera()

        #         camera.calibration_data.on_trait_change(self.update_camera_params, 'xcoeff_str')
        #         camera.calibration_data.on_trait_change(self.update_camera_params, 'ycoeff_str')
        #        camera.on_trait_change(self.parent.update_camera_params, 'focus_z')

        p = os.path.join(paths.canvas2D_dir, 'camera.cfg')
        camera.load(p)

        #        camera.current_position = (0, 0)
        camera.set_limits_by_zoom(0, 0, 0)

        vid = self.video
        if vid:
            # swap red blue channels True or False
            vid.swap_rb = camera.swap_rb

            vid.vflip = camera.vflip
            vid.hflip = camera.hflip

        self._camera_zoom_coefficients = camera.zoom_coefficients

        return camera

    def _video_default(self):
        v = Video()
        return v

    def _video_server_default(self):
        return VideoServer(video=self.video,

                           #                            port=self.video_server_port,
                           #                            quality=self.video_server_quality,
        )

    def _video_archiver_default(self):
        return Archiver()

    #    def _camera_calibration_manager_default(self):
    #        return CameraCalibrationManager()

    def _autocenter_manager_default(self):
        if self.parent.mode != 'client':
            from pychron.mv.autocenter_manager import AutoCenterManager

            return AutoCenterManager(video=self.video,
                                     canvas=self.canvas,
                                     #                                 pxpermm=self.pxpercmx / 10.,
                                     #                                    stage_controller=self.stage_controller,
                                     #                                    laser_manager=self.parent,
                                     #                                    parent=self,
                                     application=self.application
            )
        #    def _mosaic_manager_default(self):
        #        return MosaicManager(
        #                             video=self.video,
        #                                    stage_controller=self.stage_controller,
        #                                    laser_manager=self.parent,
        #                                    parent=self,
        #                                    application=self.application
        #                             )

    def _autofocus_manager_default(self):
        if self.parent.mode != 'client':
            from pychron.mv.focus.autofocus_manager import AutoFocusManager

            return AutoFocusManager(video=self.video,
                                    laser_manager=self.parent,
                                    stage_controller=self.stage_controller,
                                    canvas=self.canvas,
                                    application=self.application
            )


#===============================================================================
# calcualte camera params
#===============================================================================
# def _calculate_indicator_positions(self, shift=None):
#        ccm = self.camera_calibration_manager
#
#        zoom = self.parent.zoom
#        pychron, name = self.video_manager.snapshot(identifier=zoom)
#        ccm.image_factory(pychron=pychron)
#
#        ccm.process_image()
#        ccm.title = name
#
#        cond = Condition()
#        ccm.cond = cond
#        cond.acquire()
#        do_later(ccm.edit_traits, view='snapshot_view')
#        if shift:
#            self.stage_controller.linear_move(*shift, block=False)
#
#        cond.wait()
#        cond.release()
#
#    def _calculate_camera_parameters(self):
#        ccm = self.camera_calibration_manager
#        self._calculate_indicator_positions()
#        if ccm.result:
#            if self.calculate_offsets:
#                rdxmm = 5
#                rdymm = 5
#
#                x = self.stage_controller.x + rdxmm
#                y = self.stage_controller.y + rdymm
#                self.stage_controller.linear_move(x, y, block=True)
#
#                time.sleep(2)
#
#                polygons1 = ccm.polygons
#                x = self.stage_controller.x - rdxmm
#                y = self.stage_controller.y - rdymm
#                self._calculate_indicator_positions(shift=(x, y))
#
#                polygons2 = ccm.polygons
#
#                # compare polygon sets
#                # calculate pixel displacement
#                dxpx = sum([sum([(pts1.x - pts2.x)
#                                for pts1, pts2 in zip(p1.points, p2.points)]) / len(p1.points)
#                                    for p1, p2 in zip(polygons1, polygons2)]) / len(polygons1)
#                dypx = sum([sum([(pts1.y - pts2.y)
#                                for pts1, pts2 in zip(p1.points, p2.points)]) / len(p1.points)
#                                    for p1, p2 in zip(polygons1, polygons2)]) / len(polygons1)
#
#                # convert pixel displacement to mm using defined mapping
#                dxmm = dxpx / self.pxpercmx
#                dymm = dypx / self.pxpercmy
#
#                # calculate drive offset. ratio of request/actual
#                try:
#                    self.drive_xratio = rdxmm / dxmm
#                    self.drive_yratio = rdymm / dymm
#                except ZeroDivisionError:
#                    self.drive_xratio = 100


if __name__ == '__main__':
    from pychron.helpers.logger_setup import logging_setup

    name = 'co2'
    logging_setup('stage_manager')
    s = VideoStageManager(name='{}stage'.format(name),
                          configuration_dir_name=name,
    )
    #    i = Initializer()
    #    i.add_initialization(dict(name = 'stage_manager',
    #                              manager = s
    #                              ))
    #    i.run()

    s.load()
    s.stage_controller.bootstrap()
    # s.update_axes()

    s.configure_traits()
#============= EOF ====================================
#    def _mapcenters_button_fired(self):
#        self.info('Mapping all holes for {}'.format(self.stage_map))
#        mv = self.machine_vision_manager
#        sm = self._stage_map
#        #enumerate the current stage map holes
#        for hole in sm.sample_holes:
#            self.info('finding center of hole= {} ({},{}) '.format(hole.id,
#                                                                    hole.x,
#                                                                     hole.y))
#            self.hole = int(hole.id)
#            x = self.stage_controller._x_position
#            y = self.stage_controller._y_position
#
#            time.sleep(0.25)
#            newpos = mv.locate_target(x, y, hole.id)
#            if newpos:
#                self.info('calculated center of hole= {} ({},{}) '.format(hole.id,
#                                                                           *newpos))
#                sm.set_hole_correction(hole.id, *newpos)
#            time.sleep(0.25)
#    def _camera_coefficients_changed(self):
#        print self.camera_coefficients

#    def _calibration_manager_default(self):
#
# #        self.video.open(user = 'calibration')
#        return CalibrationManager(parent = self,
#                                  laser_manager = self.parent,
#                               video_manager = self.video_manager,
#                               )

#                adxs = []
#                adys = []
#                for p1, p2 in zip(polygons, polygons2):
# #                    dxs = []
# #                    dys = []
# #                    for pts1, pts2 in zip(p1.points, p2.points):
# #
# #                        dx = pts1.x - pts2.x
# #                        dy = pts1.y - pts2.y
# #                        dxs.append(dx)
# #                        dys.append(dy)
# #                    dxs = [(pts1.x - pts2.x) for pts1, pts2 in zip(p1.points, p2.points)]
# #                    dys = [(pts1.y - pts2.y) for pts1, pts2 in zip(p1.points, p2.points)]
# #
#                    adx = sum([(pts1.x - pts2.x) for pts1, pts2 in zip(p1.points, p2.points)]) / len(p1.points)
#                    ady = sum([(pts1.y - pts2.y) for pts1, pts2 in zip(p1.points, p2.points)]) / len(p1.points)
#
# #                    adx = sum(dxs) / len(dxs)
# #                    ady = sum(dys) / len(dys)
#                    adxs.append(adx)
#                    adys.append(ady)
#                print 'xffset', sum(adxs) / len(adxs)
#                print 'yffset', sum(adys) / len(adys)

#    def _get_drive_xratio(self):
#        return self._drive_xratio
#
#    def _set_drive_xratio(self, v):
#        self._drive_xratio = v
#        ax = self.stage_controller.axes['x']
#        ax.drive_ratio = v
#        ax.save()
#
#    def _get_drive_yratio(self):
#        return self._drive_yratio
#
#    def _set_drive_yratio(self, v):
#        self._drive_yratio = v
#        ax = self.stage_controller.axes['y']
#        ax.drive_ratio = v
#        ax.save()
