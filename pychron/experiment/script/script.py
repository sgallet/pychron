# ===============================================================================
# Copyright 2012 Jake Ross
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
from pychron.core.ui import set_qt

set_qt()
# ============= enthought library imports =======================
from traits.api import Str, Property, Button, cached_property, \
    String, HasTraits, Event, List
from traitsui.api import View, HGroup, Label, spring, EnumEditor, UItem
# ============= standard library imports ========================
import os
import yaml
import ast
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import list_directory, add_extension, remove_extension
from pychron.experiment.script.options_editor import OptionsEditor
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR
from pychron.loggable import Loggable


class ScriptOptions(HasTraits):
    names = List
    name = Str
    edit = Button

    def _names_default(self):
        return list_directory(self.options_path(), remove_extension=True)

    def traits_view(self):
        return View(HGroup(
            Label('Options'),
            spring,
            UItem('name',
                  width=-200,
                  editor=EnumEditor(name='names')),
            UItem('edit',
                  enabled_when='name and name!="---" and name is not "None"')))

    def _edit_fired(self):
        o = OptionsEditor(path=self.options_path(self.name))
        o.edit_traits()

    def options_path(self, p=None):
        r = os.path.join(paths.scripts_dir, 'options')
        if p is not None:
            r = os.path.join(r, add_extension(p, '.yaml'))
        return r


class Script(Loggable):
    # application = Any
    edit_event = Event
    refresh_lists = Event
    label = Str

    name_prefix = Property
    _name_prefix = Str
    mass_spectrometer = String
    extract_device = String

    name = Str
    # names = Property(depends_on='mass_spectrometer, directory, refresh_lists')
    names = Property(depends_on='_name_prefix, directory, refresh_lists, mass_spectrometer')
    edit = Button
    kind = 'ExtractionLine'
    shared_logger = True

    directory = Str(NULL_STR)
    directories = Property(depends_on='refresh_lists')

    def _get_name_prefix(self):
        r = ''
        if self.use_name_prefix:
            r = self._name_prefix if self._name_prefix else '{}_'.format(self.mass_spectrometer.lower())
        return r

    def _set_name_prefix(self, new):
        self._name_prefix = new

    def get_parameter(self, key, default=None):
        p = self.script_path()
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                text = rfile.read()
                m = ast.parse(text)
            docstr = ast.get_docstring(m)
            if docstr is not None:
                params = yaml.load(docstr)
                try:
                    return params[key]
                except KeyError:
                    pass
                except TypeError:
                    self.warning('Invalid yaml docstring in {}. Could not retrieve {}'.format(self.name, key))

        return default

    def script_path(self):
        if self.name_prefix:
            name = '{}{}'.format(self.name_prefix, self.name)

        name = add_extension(name, '.py')
        p = os.path.join(self._get_root(), name)

        return p

    def _edit_fired(self):
        self.edit_event = (self.script_path(), self.kind)

    def traits_view(self):
        return View(HGroup(
            Label(self.label),
            spring,
            UItem('directory',
                  width=-100,
                  editor=EnumEditor(name='directories')),
            UItem('name',
                  width=-200,
                  editor=EnumEditor(name='names')),
            UItem('edit',
                  enabled_when='name and name!="---" and name is not "None"')))

    def _clean_script_name(self, name):
        # name = self._remove_mass_spectrometer_name(name)
        if self.name_prefix:
            name = self._remove_name_prefix(name)

        return self._remove_file_extension(name)

    def _remove_file_extension(self, name):
        if name is NULL_STR:
            return NULL_STR

        return remove_extension(name)

    def _remove_name_prefix(self, name):
        if self.name_prefix:
            name = name[len(self.name_prefix):]
            # name = name.replace('{}_'.format(self.name_prefix), '')
        return name

    # def _remove_mass_spectrometer_name(self, name):
    #     if self.mass_spectrometer:
    #         name = name.replace('{}_'.format(self.mass_spectrometer.lower()), '')
    #     return name

    def _get_root(self):
        d = self.label.lower().replace(' ', '_')
        p = os.path.join(paths.scripts_dir, d)
        if self.directory != NULL_STR:
            p = os.path.join(p, self.directory)

        return p

    def _load_script_names(self):
        p = self._get_root()
        if os.path.isdir(p):
            return [s for s in os.listdir(p)
                    if not s.startswith('.') and s.endswith('.py') and s != '__init__.py']
        else:
            self.warning_dialog('{} script directory does not exist!'.format(p))

    @cached_property
    def _get_directories(self):
        p = self._get_root()
        return [NULL_STR] + [s for s in os.listdir(p)
                           if os.path.isdir(os.path.join(p, s)) and s != 'zobs']

    @cached_property
    def _get_names(self):
        names = [NULL_STR]
        # print self.name_prefix, 'asdfasdf'
        ms = self._load_script_names()
        if ms:
            # msn = '{}_'.format(self.mass_spectrometer.lower())
            # if self.kind=='Measurement':
                # print self,self.name_prefix, self.mass_spectrometer, ms
            names.extend([self._clean_script_name(ei) for ei in ms
                          if self.name_prefix and ei.startswith(self.name_prefix)])
        # print names
        return names


if __name__ == '__main__':
    paths.build('_dev')
    s = Script()
    s.label = 'extraction'
    # s.mass_spectrometer = 'jan'
    s.name_prefix = 'jan'
    s.configure_traits()

# ============= EOF =============================================
