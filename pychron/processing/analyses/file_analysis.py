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
from traits.api import Str, Property, cached_property, Float

# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import ufloat
from pychron.processing.analyses.analysis import Analysis


class NonDBAnalysis(Analysis):
    # record_id = Str
    uage = Property(depends_on='age, age_err')
    uage_wo_j_err = Property(depends_on='age, age_err')
    uuid = Str
    sample = Str

    k39 = Float
    k39_err = Float

    def get_computed_value(self, attr):
        if attr == 'k39':
            return ufloat(self.k39, self.k39_err)
        else:
            return ufloat(0, 0)

    @cached_property
    def _get_uage(self):
        return ufloat(self.age, self.age_err)

    @cached_property
    def _get_uage_wo_j_err(self):
        return self.uage


class FileAnalysis(NonDBAnalysis):
    pass


class InterpretedAgeAnalysis(NonDBAnalysis):
    pass


class SpectrumFileAnalysis(NonDBAnalysis):
    k39_value = Float
    k39_err = Float

    k39 = Property

    def get_computed_value(self, key):
        if key == 'k39':
            return self.k39
        return 0

    @cached_property
    def _get_k39(self):
        return ufloat(self.k39_value, self.k39_err)

# ============= EOF =============================================

