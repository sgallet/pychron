# ===============================================================================
# Copyright 2014 Jake Ross
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
import csv
import re
from traits.api import HasTraits, Button, Any, Instance
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
import time
from pychron.core.helpers.isotope_utils import extract_mass
from pychron.loggable import Loggable
from pychron.paths import paths


class ICMFTableGenerator(Loggable):
    def make_mftable(self, arun, detectors, refiso):
        """
            peak center `refiso` for each detector in detectors
        :return:
        """
        ion = arun.ion_optics_manager
        plot_panel = arun.plot_panel

        def func(x):
            if not x:
                ion.cancel_peak_center()

        arun.on_trait_change(func, '_alive')
        self.info('Making IC MFTable')
        results = []
        for di in detectors:
            if not arun.is_alive():
                return False

            self.info('Peak centering {}@{}'.format(di, refiso))
            ion.setup_peak_center(detector=[di], isotope=refiso, plot_panel=plot_panel, show_label=True)
            arun.peak_center = ion.peak_center
            ion.do_peak_center(new_thread=False, save=False, warn=False)
            pc = ion.peak_center_result
            if pc:
                self.info('Peak Center {}@{}={:0.6f}'.format(di, refiso, pc))
                results.append(pc)
                time.sleep(0.25)
            else:
                return False

        arun.on_trait_change(func, '_alive', remove=True)
        self._write_table(detectors, refiso, results)
        return True

    def _write_table(self, detectors, refiso, results):
        p = paths.ic_mftable
        self.info('Writing new IC MFTable to {}'.format(p))
        with open(p, 'w') as wfile:
            w = csv.writer(wfile)
            header = ['iso'] + list(detectors)
            w.writerow(header)
            w.writerow([refiso] + results)
            # m = int(extract_mass(refiso))
            # iso = refiso.replace(m, '')

            # w.writerow(['{}{}'.format(iso, m - 1)] + results)
            # w.writerow(['{}{}'.format(iso, m - 1)] + results)


# ============= EOF =============================================



