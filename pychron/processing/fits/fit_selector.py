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
from traits.has_traits import HasTraits, on_trait_change
from traits.trait_types import List, Event, Bool, Button

#============= standard library imports ========================
#============= local library imports  ==========================


from traitsui.editors import EnumEditor
from traitsui.extras.checkbox_column import CheckboxColumn as _CheckboxColumn
from traitsui.group import HGroup, VGroup
from traitsui.item import UItem, spring, Item
from traitsui.table_column import ObjectColumn as _ObjectColumn
from traitsui.view import View
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.fits.fit import Fit
from pychron.core.ui.table_editor import myTableEditor


class ColumnMixin(object):
    pass


class ObjectColumn(_ObjectColumn):
    text_font = 'modern 10'


class CheckboxColumn(_CheckboxColumn):
    text_font = 'modern 10'


class FitSelector(HasTraits):
    fits = List(Fit)
    update_needed = Event
    suppress_refresh_unknowns = Bool
    save_event = Event

    fit_klass = Fit
    command_key = Bool
    auto_update = Bool(True)

    plot_button = Button('Plot')
    default_error_type='SD'

    def _plot_button_fired(self):
        self.update_needed = True

    def _auto_update_changed(self):
        self.update_needed = True

    def _get_auto_group(self):
        return HGroup(icon_button_editor('plot_button', 'chart_curve_go',
                                         tooltip='Replot the isotope evolutions. '
                                                 'This may take awhile if many analyses are selected'),
                      icon_button_editor('save_event', 'database_save',
                                         tooltip='Save fits to database'),
                      spring,
                      Item('auto_update',
                           label='Auto Plot',
                           tooltip='Should the plot refresh after each change ie. "fit" or "show". '
                                   'It is not advisable to use this option with many analyses'))

    def traits_view(self):

        v = View(VGroup(self._get_auto_group(),
                        self._get_fit_group()))
        return v

    def _get_columns(self):
        cols = [ObjectColumn(name='name', editable=False),
                CheckboxColumn(name='show'),
                ObjectColumn(name='fit',
                             editor=EnumEditor(name='fit_types'),
                             width=150),
                ObjectColumn(name='error_type',
                             editor=EnumEditor(name='error_types'),
                             width=50),
                CheckboxColumn(name='use', label='Save DB')]

        return cols

    def _get_fit_group(self):
        cols = self._get_columns()
        editor = myTableEditor(columns=cols,
                               sortable=False,
                               on_command_key=self._update_command_key,
                               cell_bg_color='red',
                               cell_font='modern 10')
        grp = UItem('fits',
                    style='custom',
                    editor=editor)
        return grp

    @on_trait_change('fits:[show, fit, use]')
    def _fit_changed(self, obj, name, old, new):
        if self.command_key:
            for fi in self.fits:
                fi.trait_set(trait_change_notify=False,
                             **{name: new})

        if self.auto_update:
            if name in ('show', 'fit'):
                self.update_needed = True

    def load_fits(self, keys, fits):

        nfs = []
        for ki, fi in zip(keys, fits):
            pf = next((fa for fa in self.fits if fa.name == ki), None)
            fit, et, fod = fi
            if pf is None:
                pf = self.fit_klass(name=ki)

            pf.fit = fit
            pf.filter_outliers = fod.get('filter_outliers')

            pf.filter_iterations = fod.get('iterations', 0)
            pf.filter_std_devs = fod.get('std_devs', 0)
            pf.error_type = et

            nfs.append(pf)

        self.fits = nfs


    # def load_baseline_fits(self, keys):
    #     fits = self.fits
    #     if not fits:
    #         fits = []
    #
    #     fs = [
    #         self.fit_klass(name='{}bs'.format(ki), fit='average')
    #         for ki in keys]
    #
    #     fits.extend(fs)
    #     self.fits = fits

    # def add_peak_center_fit(self):
    #     fits = self.fits
    #     if not fits:
    #         fits = []
    #
    #     fs = self.fit_klass(name='PC', fit='average')
    #
    #     fits.append(fs)
    #     self.fits = fits
    #
    # def add_derivated_fits(self, keys):
    #     fits = self.fits
    #     if not fits:
    #         fits = []
    #
    #     fs = [
    #         self.fit_klass(name='{}E'.format(ki), fit='average')
    #         for ki in keys
    #     ]
    #
    #     fits.extend(fs)
    #     self.fits = fits

    def _update_command_key(self, new):
        self.command_key = new


#============= EOF =============================================
