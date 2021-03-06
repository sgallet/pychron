#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Str, Bool, Property, Int, Enum, List, String, Tuple, Float, Dict

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pychron_constants import NULL_STR, FIT_TYPES


class AuxPlotOptions(HasTraits):
    use = Bool
    name=Str(NULL_STR)
    plot_name=Property(Str, depends_on='name')

    names = List([NULL_STR,'Analysis Number Stacked','Analysis Number',
                       'Radiogenic 40Ar','K/Ca','K/Cl','Mol K39', 'Ideogram'])
    _plot_names=List(['','analysis_number_stacked', 'analysis_number', 'radiogenic_yield',
                      'kca','kcl','moles_k39','relative_probability'])

    scale = Enum('linear', 'log')
    height = Int(100, enter_set=True, auto_set=False)
    x_error = Bool(False)
    y_error = Bool(False)
    show_labels = Bool(False)
    filter_str= String(enter_set=True, auto_set=False)

    normalize = None
    use_time_axis = False
    initialized=False

    ylimits=Tuple(Float, Float, transient=True)
    overlay_positions=Dict(transient=True)
    _has_ylimits=Bool(False)

    def set_overlay_position(self, k, v):
        self.overlay_positions[k]=v

    def has_ylimits(self):
        return self._has_ylimits or (self.ylimits is not None and self.ylimits[0] !=self.ylimits[1])

    def clear_ylimits(self):
        self._has_ylimits=False
        self.ylimits=(0,0)

    def dump_yaml(self):
        d=dict()
        attrs=('use','name', 'scale','height',
               'x_error','y_error', 'show_labels','filter_str')
        for attr in attrs:
            d[attr]=getattr(self, attr)

        d['ylimits']=map(float, self.ylimits)
        d['overlay_positions']=dict(self.overlay_positions)

        return d

    def _name_changed(self):
        if self.initialized:
            if self.name != NULL_STR:
                self.use = True
                print 'setting use true', self.name

    def _get_plot_name(self):
        if self.name in self.names:
            return self._plot_names[self.names.index(self.name)]
        else:
            return self.name

    #def _get_plot_names(self):
    #    return {NULL_STR: NULL_STR,
    #            'analysis_number_stacked': 'Analysis Number Stacked',
    #            'analysis_number': 'Analysis Number',
    #            'radiogenic_yield': 'Radiogenic 40Ar',
    #            'kca': 'K/Ca',
    #            'kcl': 'K/Cl',
    #            'moles_K39': 'K39 Moles',
    #            'relative_probability': 'Ideogram'}


class FitPlotterOptions(AuxPlotOptions):
    fit = Enum(['', ] + FIT_TYPES)


class SpectrumPlotOptions(AuxPlotOptions):
    names = List([NULL_STR, '%40Ar*', 'K/Ca', 'K/Cl', 'Mol K39', 'Age'])

    _plot_names = List(['', 'radiogenic_yield', 'kca', 'kcl', 'moles_k39', 'age_spectrum'])
    #def _get_plot_names(self):
    #    return {NULL_STR: NULL_STR,
    #            'radiogenic_yield': 'Radiogenic 40Ar',
    #            'kca': 'K/Ca',
    #            'kcl': 'K/Cl',
    #            'moles_K39': 'K39 Moles',
    #            'age_spectrum': 'Age'}


class InverseIsochronPlotOptions(AuxPlotOptions):
    names = List([NULL_STR, 'Inv. Isochron'])

    _plot_names = List(['', 'inverse_isochron'])
    #def _get_plot_names(self):
    #    return {NULL_STR: NULL_STR,
                #'radiogenic_yield': 'Radiogenic 40Ar',
                #'kca': 'K/Ca',
                #'kcl': 'K/Cl',
                #'moles_K39': 'K39 Moles',
                #'inverse_isochron': 'Inv. Isochron'}


class SystemMonitorPlotOptions(AuxPlotOptions):
    _auto_set_use = False
    normalize = 'now'
    use_time_axis = True

    def _name_changed(self):
        pass

#============= EOF =============================================
