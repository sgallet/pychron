#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Instance, Button, Bool, Property, \
    on_trait_change, String, Any, DelegatesTo, List, Str
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.automated_run.uv.factory import UVAutomatedRunFactory
from pychron.experiment.automated_run.factory import AutomatedRunFactory
from pychron.experiment.queue.factory import ExperimentQueueFactory
from pychron.experiment.queue.experiment_queue import ExperimentQueue
from pychron.pychron_constants import LINE_STR
from pychron.experiment.utilities.identifier import convert_extract_device
from pychron.loggable import Loggable
from pychron.consumer_mixin import ConsumerMixin
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager


class ExperimentFactory(Loggable, ConsumerMixin):
    db = Any
    run_factory = Instance(AutomatedRunFactory)
    queue_factory = Instance(ExperimentQueueFactory)

    #     templates = DelegatesTo('run_factory')
    #     template = DelegatesTo('run_factory')

    add_button = Button('Add')
    clear_button = Button('Clear')
    save_button = Button('Save')
    edit_mode_button = Button('Edit')
    edit_enabled = DelegatesTo('run_factory')

    auto_increment_id = Bool(False)
    auto_increment_position = Bool(False)

    queue = Instance(ExperimentQueue, ())

    #    ok_run = Property(depends_on='_mass_spectrometer, _extract_device')
    ok_add = Property(depends_on='_mass_spectrometer, _extract_device, _labnumber, _username')

    _username = String
    _mass_spectrometer = String
    extract_device = String
    _labnumber = String

    selected_positions = List
    default_mass_spectrometer = Str

    #     help_label = String('Select Irradiation/Level or Project')

    #===========================================================================
    # permisions
    #===========================================================================
    #    max_allowable_runs = Int(10000)
    #    can_edit_scripts = Bool(True)
    def __init__(self, *args, **kw):
        super(ExperimentFactory, self).__init__(*args, **kw)
        self.setup_consumer(self._add_run, main=True)

    def destroy(self):
        self._should_consume = False

    def set_selected_runs(self, runs):
        self.run_factory.set_selected_runs(runs)

    def _add_run(self, *args, **kw):
        # egs = list(set([ai.extract_group for ai in self.queue.automated_runs]))
        # eg = max(egs) if egs else 0

        positions = [str(pi.positions[0]) for pi in self.selected_positions]

        load_name = self.queue_factory.load_name

        q = self.queue
        new_runs, freq = self.run_factory.new_runs(q, positions=positions,
                                                   auto_increment_position=self.auto_increment_position,
                                                   auto_increment_id=self.auto_increment_id)
        #         if self.run_factory.check_run_addition(new_runs, load_name):
        #if self.run_factory.check_run_addition(new_runs, load_name):
        # q = self.queue
        if q.selected:
            idx = q.automated_runs.index(q.selected[-1])
        else:
            idx = len(q.automated_runs) - 1

        self.queue.add_runs(new_runs, freq)

        idx += len(new_runs)

        with self.run_factory.update_selected_ctx():
            self.queue.select_run_idx(idx)

    #===============================================================================
    # handlers
    #===============================================================================
    def _clear_button_fired(self):
        self.queue.clear_frequency_runs()

    def _add_button_fired(self):
        """
            only allow add button to be fired every 0.5s

            use consumermixin.add_consumable instead of frequency limiting
        """
        self.add_consumable(5)

    def _edit_mode_button_fired(self):
        self.run_factory.edit_mode = not self.run_factory.edit_mode

        #@on_trait_change('run_factory:clear_end_after')
        #def _clear_end_after(self, new):
        #    print 'enadfas', new

    def _update_end_after(self, new):
        if new:
            for ai in self.queue.automated_runs:
                ai.end_after = False

        self.run_factory.set_end_after(new)


    @on_trait_change('''queue_factory:[mass_spectrometer,
extract_device, delay_+, tray, username, load_name, email]''')
    def _update_queue(self, name, new):
        if name == 'mass_spectrometer':
            self._mass_spectrometer = new
            self.run_factory.set_mass_spectrometer(new)

        elif name == 'extract_device':
            self._set_extract_device(new)
        elif name == 'username':
            self._username = new
            # elif name=='email':
            #     self.email=new
            #            self.queue.username = new

        if self.queue:
            self.queue.trait_set(**{name: new})

        self.queue.changed = True

    #===============================================================================
    # private
    #===============================================================================
    def _set_extract_device(self, ed):
        self.extract_device = ed
        self.run_factory = self._run_factory_factory()
        #         self.run_factory.update_templates_needed = True

        self.run_factory.load_templates()

        self.run_factory.remote_patterns = self._get_patterns(ed)
        self.run_factory.load_patterns()

        if self.queue:
            self.queue.set_extract_device(ed)
            self.queue.username = self._username
            self.queue.mass_spectrometer = self._mass_spectrometer

    def _get_patterns(self, ed):
        ps = []
        service_name = convert_extract_device(ed)
        #service_name = ed.replace(' ', '_').lower()
        man = self.application.get_service(ILaserManager, 'name=="{}"'.format(service_name))
        if man:
            ps = man.get_pattern_names()
        else:
            self.debug('No remote patterns. {} ({}) not available'.format(ed, service_name))

        return ps

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_ok_add(self):
        """
            tol should be a user permission
        """
        return self._username and \
               not self._mass_spectrometer in ('', 'Spectrometer', LINE_STR) and \
               self._labnumber

    #===============================================================================
    #
    #===============================================================================
    def _run_factory_factory(self):
        if self.extract_device == 'Fusions UV':
            klass = UVAutomatedRunFactory
        else:
            klass = AutomatedRunFactory

        rf = klass(db=self.db,
                   application=self.application,
                   extract_device=self.extract_device,
                   mass_spectrometer=self.default_mass_spectrometer)

        rf.load_truncations()
        rf.on_trait_change(lambda x: self.trait_set(_labnumber=x), 'labnumber')
        rf.on_trait_change(self._update_end_after, 'end_after')
        return rf

    #    def _can_edit_scripts_changed(self):
    #        self.run_factory.can_edit = self.can_edit_scripts

    #===============================================================================
    # defaults
    #===============================================================================
    def _run_factory_default(self):
        return self._run_factory_factory()

    def _queue_factory_default(self):
        eq = ExperimentQueueFactory(db=self.db)
        return eq

    def _db_changed(self):
        self.queue_factory.db = self.db
        self.run_factory.db = self.db

    def _default_mass_spectrometer_changed(self):
        self.run_factory.set_mass_spectrometer(self.default_mass_spectrometer)
        self.queue_factory.mass_spectrometer = self.default_mass_spectrometer
        self._mass_spectrometer = self.default_mass_spectrometer
        #============= EOF =============================================
