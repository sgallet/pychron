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
from pychron.core.helpers.filetools import to_bool

#============= enthought library imports =======================
from scipy import optimize
from traits.api import HasTraits, List, Any, Property, Float, Event, Str, Bool
from traitsui.api import View, Item, VGroup, HGroup, Spring, \
    RangeEditor

#============= standard library imports ========================
import os
import csv
import time
from numpy import min, nonzero, array, asarray
#============= local library imports  ==========================
from pychron.paths import paths
# import math
# from pychron.graph.graph import Graph
from pychron.spectrometer.spectrometer_device import SpectrometerDevice
# from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS
# from pychron.core.regression.ols_regressor import PolynomialRegressor

class CalibrationPoint(HasTraits):
    x = Float
    y = Float


def get_float(func):
    def dec(*args, **kw):
        try:
            return float(func(*args, **kw))
        except (TypeError, ValueError):
            pass

    return dec


def get_detector_name(det):
    if not isinstance(det, (str, unicode)):
        det = det.name
    return det


def mass_cal_func(p, x):
    return p[2] + (p[0] ** 2 * x / p[1]) ** 0.5


def least_squares(func, xs, ys, initial_guess):
    xs, ys = asarray(xs), asarray(ys)
    errfunc = lambda p, x, v: func(p, x) - v
    ret, info = optimize.leastsq(errfunc, initial_guess, args=(xs, ys))
    return ret


class Magnet(SpectrometerDevice):
    _mftable = None

    dac = Property(depends_on='_dac')
    mass = Property(depends_on='_mass')

    _dac = Float
    _mass = Float
    dacmin = Float(0.0)
    dacmax = Float(10.0)

    massmin = Property(Float, depends_on='_massmin')
    massmax = Property(Float, depends_on='_massmax')
    _massmin = Float(0.0)
    _massmax = Float(200.0)

    settling_time = 0.5

    calibration_points = List  # Property(depends_on='mftable')
    detector = Any

    dac_changed = Event

    fitfunc = Str('parabolic')

    protected_detectors=List

    use_detector_protection=Bool
    use_beam_blank=Bool

    detector_protection_threshold=Float(0.1) #DAC units
    beam_blank_threshold=Float(0.1) #DAC units

    def update_field_table(self, det, isotope, dac):
        """

            dac needs to be in axial units
        """
        det = get_detector_name(det)

        self.info('update mftable {} {}'.format(isotope, dac))

        d, header = self._get_mftable()

        isos, xs, ys = map(array, d[det][:3])

        try:
            refindex = min(nonzero(isos == isotope)[0])

            delta = dac - ys[refindex]
            # need to calculate all ys
            # using simple linear offset
            #ys += delta
            for k, (iso, xx, yy, _) in d.iteritems():
                ny = yy + delta
                p = least_squares(mass_cal_func, xx, ny, [ny[0], xx[0], 0])
                d[k] = iso, xx, ny, p

            self.dump(isos, header, d)
            #self._mftable = isos, xs, ys

        except ValueError:
            import traceback

            e = traceback.format_exc()
            self.debug('Magnet update field table {}'.format(e))

    #===============================================================================
    # ##positioning
    #===============================================================================
    def set_dac(self, v, verbose=False):
        micro = self.microcontroller
        unprotect = False
        unblank=False
        if micro:
            if self.use_detector_protection:
                if abs(self._dac - v) >self.detector_protection_threshold:
                    for pd in self.protected_detectors:
                        micro.ask('ProtectDetector {},On'.format(pd), verbose=verbose)
                    unprotect = True

            elif self.use_beam_blank:
                if abs(self._dac - v) >self.beam_blank_threshold:
                    micro.ask('BlankBeam True', verbose=verbose)
                    unblank=True

            micro.ask('SetMagnetDAC {}'.format(v), verbose=verbose)
            time.sleep(self.settling_time)

            #only block if move is large and was made slowly.
            #this should be more explicit. get MAGNET_MOVE_THRESHOLD from RCS
            # and use it as to test whether to GetMagnetMoving
            if unprotect or unblank:
                for i in xrange(50):
                    if not to_bool(micro.ask('GetMagnetMoving')):
                        break
                    time.sleep(0.25)

                if unprotect:
                    for pd in self.protected_detectors:
                        micro.ask('ProtectDetector {},Off'.format(pd), verbose=verbose)
                if unblank:
                    micro.ask('BlankBeam False', verbose=verbose)

        self._dac = v
        self.dac_changed = True

    @get_float
    def read_dac(self):
        if self.microcontroller is None:
            r = 0
        else:
            r = self.microcontroller.ask('GetMagnetDAC')
        return r

    #===============================================================================
    # persistence
    #===============================================================================
    def load(self):
        pass


    def finish_loading(self):
        d = self.read_dac()
        if d is not None:
            self._dac = d

    def dump(self, isos, header, d):
        p = os.path.join(paths.spectrometer_dir, 'mftable.csv')
        with open(p, 'w') as f:
            writer = csv.writer(f)

            writer.writerow(['iso'] + header)

            for i, iso in enumerate(isos):
                a = [iso]
                for hi in header:
                    iso, xs, ys, _ = d[hi]
                    a.append(ys[i])

                writer.writerow(a)

    #===============================================================================
    # mapping
    #===============================================================================
    def map_dac_to_mass(self, dac, detname):
        detname = get_detector_name(detname)

        d, _ = self._get_mftable()
        _, xs, ys, p = d[detname]

        def func(x, *args):
            c = list(p)
            c[-1] -= dac
            return mass_cal_func(c, x)

        mass = optimize.brentq(func, 0, 200)
        return mass

    def map_mass_to_dac(self, mass, detname):
        detname = get_detector_name(detname)
        d, _ = self._get_mftable()
        _, xs, ys, p = d[detname]
        dac = mass_cal_func(p, mass)

        self.debug('map mass to dac {} >> {}'.format(mass, dac))

        return dac

    def map_dac_to_isotope(self, dac=None, det=None, current=True):
        if dac is None:
            dac = self._dac
        if det is None:
            det = self.detector

        if det:
            dac = self.spectrometer.uncorrect_dac(det, dac, current=current)

        m = self.map_dac_to_mass(dac, det.name)
        molweights = self.spectrometer.molecular_weights
        return next((k for k, v in molweights.iteritems() if abs(v - m) < 0.001), None)

    def _get_mftable(self):
        if not self._mftable:
            self._mftable = self._load_mftable()

        return self._mftable

    def _load_mftable(self):
        p = os.path.join(paths.spectrometer_dir, 'mftable.csv')
        self.info('loading mftable {}'.format(p))
        if os.path.isfile(p):
            with open(p, 'U') as f:
                reader = csv.reader(f)
                if self.spectrometer:
                    molweights = self.spectrometer.molecular_weights
                else:
                    from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS as molweights

                header = map(str.strip, reader.next()[1:])
                d = {}
                for line in reader:
                    iso = line[0]
                    try:
                        mw = molweights[iso]
                    except KeyError:
                        continue

                    for i, li in enumerate(line[1:]):
                        hi = header[i]
                        try:
                            li = float(li)
                        except (TypeError, ValueError):
                            continue

                        if hi in d:
                            isos, xs, ys = d[hi]
                            isos.append(iso)
                            xs.append(mw)
                            ys.append(li)
                        else:
                            d[hi] = [iso], [mw], [li]

            for k, (isos, xs, ys) in d.iteritems():
                cs = least_squares(mass_cal_func, xs, ys, [ys[0], xs[0], 0])
                d[k] = (isos, xs, ys, cs)

            return d, header
        else:
            self.warning_dialog('No Magnet Field Table. Create {}'.format(p))

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_mass(self):
        return self._mass

    def _set_mass(self, m):
        if self.detector:
            dac = self.map_mass_to_dac(m, self.detector.name)
            dac = self.spectrometer.correct_dac(self.detector, dac)
            self._mass = m
            self.dac = dac

    def _validate_dac(self, d):
        return self._validate_float(d)

    def _get_dac(self):
        return self._dac

    def _set_dac(self, v):
        if v is not None:
            self.set_dac(v)

    def _validate_float(self, d):
        try:
            return float(d)
        except (ValueError, TypeError):
            return d

    def _validate_massmin(self, d):
        d = self._validate_float(d)
        if isinstance(d, float):
            if d > self.massmax:
                d = str(d)
        return d

    def _get_massmin(self):
        return self._massmin

    def _set_massmin(self, v):
        self._massmin = v

    def _validate_massmax(self, d):
        d = self._validate_float(d)
        if isinstance(d, float):
            if d < self.massmin:
                d = str(d)
        return d

    def _get_massmax(self):
        return self._massmax

    def _set_massmax(self, v):
        self._massmax = v

    #===============================================================================
    # views
    #===============================================================================
    def traits_view(self):
        v = View(
            VGroup(
                VGroup(
                    Item('dac', editor=RangeEditor(low_name='dacmin',
                                                   high_name='dacmax',
                                                   format='%0.5f')),

                    Item('mass', editor=RangeEditor(mode='slider', low_name='massmin',
                                                    high_name='massmax',
                                                    format='%0.3f')),
                    HGroup(Spring(springy=False,
                                  width=48),
                           Item('massmin', width=-40), Spring(springy=False,
                                                              width=138),
                           Item('massmax', width=-55),

                           show_labels=False),
                    show_border=True,
                    label='Control'
                ),
                #                     Group(Item('scanner', style='custom', show_label=False),
                #                           label='Scanner',
                #                           show_border=True)
            )
        )

        return v

        #     def _get_calibration_points(self):
        #         if self.mftable is not None:
        #             molweights = MOLECULAR_WEIGHTS
        # #            molweights = self.spectrometer.molecular_weights
        #             xs, ys = self.mftable
        #             return [CalibrationPoint(x=molweights[xi], y=yi) for xi, yi in zip(xs, ys)]
        #def mftable_view(self):
        #    cols = [ObjectColumn(name='x', label='Mass'),
        #            ObjectColumn(name='y', label='DAC')]
        #
        #    teditor = TableEditor(columns=cols, editable=False)
        #    v = View(HGroup(
        #        Item('calibration_points', editor=teditor, show_label=False),
        #        Item('graph', show_label=False, style='custom')),
        #             width=700,
        #             height=500,
        #             resizable=True)
        #    return v


# if __name__ == '__main__':
#     from launchers.helpers import build_version
#
#     build_version('_dev')
#
#     from pychron.core.helpers.logger_setup import logging_setup
#
#     logging_setup('magnet')
#     m = Magnet()
#     m.load()
#     m.update_field_table('AX', 'Ar40', 5)
    #m.configure_traits()
    #============= EOF =============================================
    # def get_dac_for_mass(self, mass):
    #        reg = self.regressor
    #        data = [[MOLECULAR_WEIGHTS[i] for i in self.mftable[0]],
    #                self.mftable[1]
    #                ]
    #        if isinstance(mass, str):
    #            mass = MOLECULAR_WEIGHTS[mass]
    #
    #        if data:
    #            dac_value = reg.get_value('parabolic', data, mass)
    #        else:
    #            dac_value = 4
    #
    #        return dac_value
    #
    #    def set_axial_mass(self, x, hv_correction=1, dac=None):
    #        '''
    #            set the axial detector to mass x
    #        '''
    #        reg = self.regressor
    #
    #        if dac is None:
    #            data = [[MOLECULAR_WEIGHTS[i] for i in self.mftable[0]],
    #                    self.mftable[1]
    #                    ]
    #            dac = reg.get_value('parabolic', data, x) * hv_correction
    #
    #        #print x, dac_value, hv_correction
    #
    #        self.set_dac(dac)
    #    def set_graph(self, pts):
    #
    #        g = Graph(container_dict=dict(padding=10))
    #        g.clear()
    #        g.new_plot(xtitle='Mass',
    #                   ytitle='DAC',
    #                   padding=[30, 0, 0, 30],
    #                   zoom=True,
    #                   pan=True
    #                   )
    #        g.set_x_limits(0, 150)
    #        g.set_y_limits(0, 100)
    #        xs = [cp.x for cp in pts]
    #        ys = [cp.y * 10 for cp in pts]
    #
    #        reg = self.regressor
    #        rdict = reg.parabolic(xs, ys, data_range=(0, 150), npts=5000)
    #
    #        g.new_series(x=xs, y=ys, type='scatter')
    #
    #
    #        g.new_series(x=rdict['x'], y=rdict['y'])
    #        self.graph = g
    #    def calculate_dac(self, pos):
    #        #is pos a number
    #        if not isinstance(pos, (float, int)):
    #            #is pos a isokey or a masskey
    #            # eg. Ar40, or 39.962
    #            mass = None
    #            isokeys = {'Ar40':39.962}
    #            try:
    #                mass = isokeys[pos]
    #            except KeyError:
    #                try:
    #                    mass = float(pos)
    #                except:
    #                    self.debug('invalid magnet position {}'.format(pos))
    #
    #            print 'ionpt', mass, pos,
    #            pos = self.map_mass_to_dac(mass)
    #            print pos

    #        return pos