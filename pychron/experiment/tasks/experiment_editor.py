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
from traits.api import Instance, Unicode, Property, DelegatesTo
from traitsui.api import View, UItem

#============= standard library imports ========================
import os
#============= local library imports  ==========================

from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.experiment.automated_run.tabular_adapter import AutomatedRunSpecAdapter, UVAutomatedRunSpecAdapter
from pychron.experiment.queue.experiment_queue import ExperimentQueue
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.core.helpers.filetools import add_extension


class ExperimentEditor(BaseTraitsEditor):
    queue = Instance(ExperimentQueue, ())  # Any
    path = Unicode

    name = Property(Unicode, depends_on='path')
    tooltip = Property(Unicode, depends_on='path')

    executed = DelegatesTo('queue')
    tabular_adapter_klass = AutomatedRunSpecAdapter
    #     merge_id = Int(0)
    #     group = Int(0)

    #     dirty = Bool(False)

    #    def create(self, parent):
    #        self.control = self._create_control(parent)

    def _dirty_changed(self):
        self.debug('dirty changed {}'.format(self.dirty))

    def traits_view(self):

        arun_grp = UItem('automated_runs',
                         editor=myTabularEditor(adapter=self.tabular_adapter_klass(),
                                                operations=['delete',
                                                            'move'],
                                                editable=True,
                                                dclicked='dclicked',
                                                selected='selected',
                                                paste_function='paste_function',
                                                refresh='refresh_table_needed',
                                                scroll_to_row='automated_runs_scroll_to_row',
                                                copy_cache='linked_copy_cache',
                                                multi_select=True),
                         height=200)

        executed_grp = UItem('executed_runs',
                             editor=myTabularEditor(adapter=self.tabular_adapter_klass(),
                                                    editable=False,
                                                    auto_update=True,
                                                    selectable=True,
                                                    copy_cache='linked_copy_cache',
                                                    selected='executed_selected',
                                                    multi_select=True,
                                                    scroll_to_row='executed_runs_scroll_to_row'
                             ),
                             height=500,
                             visible_when='executed'
        )

        v = View(
            #                 VGroup(
            executed_grp,
            arun_grp,
            #                     ),
            resizable=True
        )
        return v


    def trait_context(self):
        """ Use the model object for the Traits UI context, if appropriate.
        """
        if self.queue:
            return {'object': self.queue}
        return super(ExperimentEditor, self).trait_context()

    #    @on_trait_change('queue:automated_runs[], queue:changed')
    def _queue_changed(self):
    #        f = lambda: self.trait_set(dirty=True)
        f = self._set_queue_dirty
        self.queue.on_trait_change(f, 'automated_runs[]')
        self.queue.on_trait_change(f, 'changed')
        self.queue.path = self.path

    def _path_changed(self):
        self.queue.path = self.path

    def _set_queue_dirty(self, obj, name, old, new):
    #         print 'ggg', obj, name, old, new
    #         print 'set qirty', self.queue._no_update, self.queue.initialized

        if not self.queue._no_update and self.queue.initialized:
            self.dirty = True

            #===========================================================================
            #
            #===========================================================================

    def new_queue(self, txt=None, **kw):
        queue = self.queue_factory(**kw)
        if txt:
            if queue.load(txt):
                self.queue = queue
        else:
            self.queue = queue

    def queue_factory(self, **kw):
        return ExperimentQueue(**kw)

    def save(self, path, queues=None):
        if queues is None:
            queues = [self.queue]

        if self._validate_experiment_queues(queues):
            path = self._dump_experiment_queues(path, queues)
            if path:
                self.path = path
                self.dirty = False

                return True

    def _validate_experiment_queues(self, eqs):
        # check runs
        for qi in eqs:
            hec=qi.human_error_checker

            qi.executable = True
            qi.initialized = True

            err = hec.check_runs(qi.cleaned_automated_runs, test_all=True,
                                 test_scripts=True)
            if err:
                qi.executable = False
                qi.initialized = False
                hec.report_errors(err)
                #self.information_dialog(err)
                break

            err = hec.check_queue(qi)
            if err:
                self.warning_dialog(err)
                break

        else:
            return True

    def _dump_experiment_queues(self, p, queues):

        if not p:
            return

        p = add_extension(p)

        self.info('saving experiment to {}'.format(p))
        with open(p, 'wb') as fp:
            n = len(queues)
            for i, exp in enumerate(queues):
                exp.path = p
                exp.dump(fp)
                if i < (n - 1):
                    fp.write('\n')
                    fp.write('*' * 80)

        return p


    #===============================================================================
    # handlers
    #===============================================================================
    #    def _path_changed(self):
    #        '''
    #            parse the file at path
    #        '''
    #        if os.path.isfile(self.path):
    #            with open(self.path) as fp:
    #                txt = fp.read()
    #                queues = self._parse_text(txt)
    #                for qi in queues:
    #                    qu=self.new_queue()
    #                    exp.load(text):


    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_tooltip(self):
        return self.path

    def _get_name(self):
        if self.path:
            name = os.path.basename(self.path)
            name, _ = os.path.splitext(name)
        #             if self.merge_id:
        #                 name = '{}-{:02n}'.format(name, self.merge_id)
        else:
            name = 'Untitled'
        return name


class UVExperimentEditor(ExperimentEditor):
    tabular_adapter_klass = UVAutomatedRunSpecAdapter

#============= EOF =============================================
