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
from traits.api import HasTraits, Float, Str, Any, List
# ============= standard library imports ========================
# ============= local library imports  ==========================


class Point(HasTraits):
    x = Float
    y = Float


class Polygon(object):
    points = None


class SamplePoint(Point):
    sample=Str
    identifier=Str
    material=Str
    lithology=Str


class AgePoint(SamplePoint):
    age=Float
    age_error=Float
    age_kind=Str
    interpreted_age=Any
    interpreted_ages=List

    def _interpreted_age_changed(self):
        self.age=self.interpreted_age.age
        self.age_error=self.interpreted_age.age
        self.age_kind=self.interpreted_age.kind


# ============= EOF =============================================

