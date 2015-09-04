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

# ============= standard library imports ========================
# ============= local library imports  ==========================
import os

from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout
import yaml

from pychron.processing.tasks.browser.browser_task import BaseBrowserTask
from pychron.processing.tasks.browser.util import browser_pane_item
from pychron.processing.tasks.interpreted_age.actions import SaveInterpretedAgeGroupAction, \
    OpenInterpretedAgeGroupAction, SaveAsInterpretedAgeGroupAction, MakeGroupFromFileAction, \
    DeleteInterpretedAgeGroupAction, \
    PlotIdeogramAction, MakeGroupAction, SaveTablesAction
from pychron.processing.tasks.interpreted_age.interpreted_age_editor import InterpretedAgeEditor
from pychron.processing.tasks.interpreted_age.group_dialog import SaveGroupDialog, OpenGroupDialog, DeleteGroupDialog
from pychron.processing.tasks.interpreted_age.table_selection_dialog import TableSelectionDialog
from pychron.processing.tasks.interpreted_age.tas_writer import TASWriter


class InterpretedAgeTask(BaseBrowserTask):
    name = 'Interpreted Ages'
    id = 'pychron.processing.interpreted_age'
    tool_bars = [SToolBar(SaveTablesAction()),
                 # SToolBar(SavePDFTablesAction(),
                 #          SaveXLSTablesAction()),
                 SToolBar(SaveAsInterpretedAgeGroupAction(),
                          SaveInterpretedAgeGroupAction(),
                          OpenInterpretedAgeGroupAction(),
                          DeleteInterpretedAgeGroupAction()),
                 SToolBar(MakeGroupAction(),
                          MakeGroupFromFileAction()),
                 SToolBar(PlotIdeogramAction())]

    def plot_ideogram(self):
        if self.active_editor:
            iages = self.active_editor.interpreted_ages
            if iages:
                task = self.window.application.get_task('pychron.processing.figures')
                task.new_ideogram()

                task.active_editor.plot_interpreted_ages(iages)

    def external_delete_group(self):
        self.load_projects()
        self.delete_group()

    def delete_group(self):

        dlg = DeleteGroupDialog(projects=self.projects,
                                oprojects=self.projects,
                                db=self.manager.db)
        info = dlg.edit_traits(kind='livemodal')
        if info.result:
            ids = dlg.get_selected_ids()
            if ids:
                if self.confirmation_dialog('Are you sure to want to delete the selected groups?'):
                    editor = InterpretedAgeEditor(processor=self.manager)
                    editor.delete_groups(ids)

    def make_tas(self):
        if self.has_active_editor():
            tw = TASWriter()
            db = self.manager.db
            tw.write(db, self.active_editor.interpreted_ages)

    def make_group_from_selected(self):
        if self.has_active_editor():
            if self.selected_samples:
                lns = [si.identifier for si in self.selected_samples]
                self.active_editor.add_latest_interpreted_ages(lns)
            else:
                self.information_dialog('Please select a set of samples.')

    def make_group_from_file(self):
        if self.has_active_editor():
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages_lt8_no_int.yaml'
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages_gt8_no_int.yaml'
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages_all.yaml'
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages_all2.yaml'
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/interpreted_ages_all3.yaml'
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/interpreted_ages_all4.yaml'
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/interpreted_ages_all5.yaml'
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/interpreted_ages_all7.yaml'
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/interpreted_ages_all8.yaml'
            p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/all_ages.yaml'
            if not os.path.isfile(p):
                p = self.open_file_dialog()
            if p:
                with open(p, 'r') as rfile:
                    d = yaml.load(rfile)

                project = d['project']
                name = d['name']
                ids = d['interpreted_age_ids']
                self.active_editor.save_group(name, project, ids=ids)

                self.db_save_info()

    def external_open_interpreted_age_group(self):
        self.load_projects()
        ogd = OpenGroupDialog(projects=self.projects,
                              oprojects=self.projects,
                              db=self.manager.db)
        info = ogd.edit_traits(kind='livemodal')
        if info.result:
            return ogd.get_selected_ids()

    def open_interpreted_age_group(self):
        if self.has_active_editor():
            ogd = OpenGroupDialog(projects=self.projects,
                                  oprojects=self.projects,
                                  db=self.manager.db)
            if self.selected_projects:
                ogd.selected_project = self.selected_projects[-1]

            info = ogd.edit_traits(kind='livemodal')
            if info.result:
                ids = ogd.get_selected_ids()
                if ids:
                    self.open_interpreted_age_groups(ids)

    def open_interpreted_age_groups(self, gids):
        if self.has_active_editor():
            self.active_editor.open_group(gids[0])
            for i in gids[1:]:
                editor = self._new_editor()
                editor.open_group(i)

    def save_interpreted_age_group(self):
        if self.has_active_editor():
            if self.active_editor.saved_group_id:
                self.active_editor.update_group()
            else:
                self.save_as_interpreted_age_group()
            self.db_save_info()

    def save_as_interpreted_age_group(self):
        if self.has_active_editor():
            if self.active_editor.interpreted_ages:

                sgd = SaveGroupDialog(projects=self.projects)
                if self.selected_projects:
                    sgd.selected_project = self.selected_projects[-1]

                info = sgd.edit_traits(kind='livemodal')
                if info.result:
                    name = sgd.name
                    project = sgd.selected_project.name
                    if name and project:
                        self.active_editor.save_group(name, project)

    def save_tables(self):
        if self.has_active_editor():
            t = TableSelectionDialog()
            info = t.edit_traits(kind='livemodal')
            if info.result:
                self.active_editor.save_tables(t.model)

    # def save_xls_tables(self):
    #     if self.has_active_editor():
    #         n = self.active_editor.name
    #         #p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/{}.pdf'.format(n)
    #         r = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/test'
    #         if not os.path.isdir(r):
    #             p = self.save_file_dialog(ext='.xls')
    #         else:
    #             p, _ = unique_path(r, n, extension='.xls')
    #
    #         if p:
    #             self.active_editor.save_xls_tables(p)
    #
    #             # self.view_xls(p)
    #
    # def save_pdf_tables(self):
    #     if self.has_active_editor():
    #         # p=self.save_file_dialog()
    #         # p = '/Users/ross/Sandbox/interpreted_age.pdf'
    #
    #         n = self.active_editor.name
    #         #p = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/{}.pdf'.format(n)
    #         r = '/Users/ross/Programming/git/dissertation/data/minnabluff/interpreted_ages/test'
    #         if not os.path.isdir(r):
    #             p = self.save_file_dialog(ext='.pdf')
    #         else:
    #             p, _ = unique_path(r, n, extension='.pdf')
    #
    #         if p:
    #             self.active_editor.save_pdf_tables(p)
    #
    #             # self.view_pdf(p)

    def create_dock_panes(self):
        panes = [self._create_browser_pane(analyses_defined='0')]

        return panes

    def _new_editor(self):
        editor = InterpretedAgeEditor(processor=self.manager)
        self._open_editor(editor)
        return editor

    def _selected_samples_changed(self):
        if not self.active_editor:
            self._new_editor()

        self.active_editor.set_samples(self.selected_samples)

    def _default_layout_default(self):
        return TaskLayout(left=browser_pane_item())

# ============= EOF =============================================

