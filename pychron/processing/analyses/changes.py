# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, Date, Str, List, Long, Any, Float, Bool, Event
# ============= standard library imports ========================
# ============= local library imports  ==========================


class Change(HasTraits):
    create_date = Date
    summary = Str
    id = Long
    active = Bool(False)

    def __init__(self, dbrecord=None, *args, **kw):
        super(Change, self).__init__(*args, **kw)
        if dbrecord:
            self.create_date = dbrecord.create_date
            self.id = dbrecord.id
            self._make_summary(dbrecord)


class IsotopeBlankRecord(HasTraits):
    isotope = Str
    fit = Str
    id = Long
    analyses = List
    value = Float
    error = Float


class AnalysisRecord(HasTraits):
    id = Long
    record_id = Str


class ValueRecord(HasTraits):
    value = Float
    error = Float
    timestamp = Float


class FitRecord(HasTraits):
    isotope = Str
    fit = Str


class BlankChange(Change):
    isotopes = List
    # analyses = Property(List, depends_on='selected')
    selected = Any
    load_analyses_needed = Event

    def _selected_default(self):
        return IsotopeBlankRecord()

    def _make_summary(self, dbrecord):
        s = ', '.join([bi.make_summary() for bi in dbrecord.blanks])
        self.summary = s

        def afactory(b):
            return [AnalysisRecord(id=ai.analysis.id,
                                   record_id=ai.analysis.record_id) for ai in b.analysis_set]

        def vfactory(b):
            return [ValueRecord(value=ai.value, error=ai.error,
                                timestamp=ai.analysis.timestamp) for ai in b.value_set]

        self.isotopes = [IsotopeBlankRecord(id=bi.id, isotope=bi.isotope,
                                            # analyses=afactory(bi),
                                            value=bi.user_value,
                                            error=bi.user_error,
                                            values=vfactory(bi),
                                            fit=bi.fit or 'Pr') for bi in dbrecord.blanks]

        self.selected = next((hi for hi in self.isotopes if hi.isotope == 'Ar40'), self.isotopes[-1])

        b = next((bi for bi in dbrecord.blanks if bi.isotope == 'Ar40'), dbrecord.blanks[-1])
        self.selected.analyses = afactory(b)

    def _selected_changed(self):
        self.load_analyses_needed = self.selected


class FitChange(Change):
    fits = List

    def _make_summary(self, dbrecord):
        s = ', '.join([fi.make_summary() for fi in dbrecord.fits])
        self.summary = s
        self.fits = [FitRecord(isotope=fi.isotope_label, fit=fi.fit) for fi in dbrecord.fits]


# ============= EOF =============================================

