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
import os

from traits.api import List, Int


# ============= standard library imports ========================
# ============= local library imports  ==========================
import yaml
from pychron.paths import paths
from pychron.loggable import Loggable


doc_mapping = ['setup', 'import', 'iso_fits',
               'blanks', 'disc', 'ic',
               'figures', 'tables', 'flux',
               'sensitivity']


class EasyParser(Loggable):
    _docs = List
    _ndocs = Int

    def __init__(self, path=None, name=None, *args, **kw):
        super(EasyParser, self).__init__(*args, **kw)
        # if name is None:
        #     name = 'minna_bluff_prj3'

        # name = add_extension(name, '.yaml')
        # p = os.path.join(paths., name)
        if path is None:
            path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'spectra_unknowns.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'flux.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'ideo_j_grouped.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'ideo_unknowns.yaml')
            path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'ideo_unknowns_grouped.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'spec_unknowns_grouped.yaml')
            path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'integrated_unknowns_grouped.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'gee_unknowns_grouped.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'gee_ideo.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'results_spec_unknowns_grouped.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'results_ideo_unknowns_grouped.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'results_spec_plag_unknowns_grouped.yaml')

            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'compare_iso_spec.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'isochron_unknowns.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'disc_j.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'disc_unknowns.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'fit_unknowns.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'fit_j.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'blank_j.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'blank_unknowns.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'flux.yaml')

            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'ideo_unknowns.yaml')
            # path = os.path.join(paths.dissertation, 'data', 'minnabluff', 'spectra_unknowns.yaml')

        if os.path.isfile(path):
            with open(path, 'r') as rfile:
                md = yaml.load_all(rfile)
                self._docs = list(md)
                self._ndocs = len(self._docs)
        else:
            self.warning_dialog('Invalid EasyParser file. {}'.format(path))

    def doc(self, idx):

        if isinstance(idx, str):
            try:
                idx = doc_mapping.index(idx)
            except ValueError:
                self.warning_dialog('Invalid Document index {}. ndocs={}'.format(idx, ','.join(doc_mapping)))
                return

        try:
            return self._docs[idx]
        except IndexError:
            self.warning_dialog('Invalid Document index {}. ndocs={}'.format(idx, self._ndocs))

# ============= EOF =============================================

