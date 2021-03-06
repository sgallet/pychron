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
from itertools import groupby
from datetime import timedelta
import binascii

from enable.component import Component
from pyface.tasks.action.schema import SToolBar
from traits.api import Instance, on_trait_change, List

from pychron.core.helpers.iterfuncs import partition
from pychron.easy_parser import EasyParser
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.processing.tasks.actions.edit_actions import DatabaseSaveAction
from pychron.processing.tasks.analysis_edit.panes import UnknownsPane, ControlsPane, \
    TablePane
from pychron.processing.tasks.analysis_edit.tags import Tag
from pychron.processing.tasks.browser.browser_task import BaseBrowserTask
from pychron.processing.tasks.browser.panes import AnalysisAdapter
from pychron.processing.tasks.recall.recall_editor import RecallEditor
from pychron.processing.tasks.analysis_edit.adapters import UnknownsAdapter









# from pyface.tasks.task_window_layout import TaskWindowLayout
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.processing.tasks.analysis_edit.plot_editor_pane import PlotEditorPane
from pychron.processing.analyses.analysis import Analysis

#============= standard library imports ========================
#============= local library imports  ==========================

from traits.api import HasTraits, Str, Property
from traitsui.api import View, Item, UItem, HGroup, TabularEditor


class AnalysisGroupEntry(HasTraits):
    name = Str
    items = List
    analyses = Property
    analysis_type = Str

    def _get_analyses(self):
        return ((self.items, self.analysis_type),)

    def set_items(self, ans):
        items, at = ans[0]
        self.items = items
        self.analysis_type = at

    def traits_view(self):
        v = View(
            HGroup(Item('name', label='Analysis Group Name')),
            UItem('items', editor=TabularEditor(adapter=AnalysisAdapter())),
            resizable=True,
            buttons=['OK', 'Cancel'],
            kind='livemodal',
            title='Analysis Group Entry')
        return v


class AnalysisEditTask(BaseBrowserTask):
    id = 'pychron.processing'
    unknowns_pane = Instance(TablePane)
    controls_pane = Instance(ControlsPane)
    plot_editor_pane = Instance(PlotEditorPane)
    unknowns_adapter = UnknownsAdapter
    unknowns_pane_klass = UnknownsPane

    ic_factor_editor_count = 0

    tool_bars = [SToolBar(DatabaseSaveAction(),
                          # FindAssociatedAction(),
                          image_size=(16, 16))]

    external_recall_window = False
    _tag_table_view = None

    analysis_group_edit_klass = AnalysisGroupEntry

    def add_iso_evo(self, name=None, rec=None):
        if rec is None:
            if self.active_editor is not None:
                rec = self.active_editor.model
                name = self.active_editor.name

        if rec is None:
            return

        from pychron.processing.tasks.isotope_evolution.isotope_evolution_editor import IsotopeEvolutionEditor

        name = 'IsoEvo {}'.format(name)
        editor = self.get_editor(name)
        if editor:
            self.activate_editor(editor)
        else:
            ieditor = IsotopeEvolutionEditor(name=name, processor=self.manager)
            ieditor.set_items([rec])
            self.editor_area.add_editor(ieditor)

    def set_analysis_group(self):
        ans = self._get_analyses_to_group()

        if not ans:
            self.information_dialog('No analyses selected to group')
            return

        a = self.analysis_group_edit_klass()
        # print ans
        a.set_items(ans)

        info = a.edit_traits()
        if info.result:
            name = a.name

            db = self.manager.db

            uuids = [ai.uuid for ais, k in ans
                     for ai in ais]

            with db.session_ctx():
                aa = db.get_analyses(pred=lambda m, l: (m.uuid.in_(uuids), ))
                set_id = binascii.crc32(''.join([ai.uuid for ai in aa]))

                dbg = db.get_analysis_group(set_id, key='id')
                if dbg is not None:
                    msg = 'Analysis Group of these analyses already exists. Name={}'.format(dbg.name)
                    self.information_dialog(msg)
                    return

                group = db.add_analysis_group(name, id=set_id)
                self._set_analysis_group(db, group, a.analyses)
                self.db_save_info()

                self._load_associated_groups(self.selected_projects)

    def _set_analysis_group(self, db, group, ans):
        # db=self.manager.db
        for ais, at in ans:
            at = db.get_analysis_type(at)
            self.debug('set analysis group for {} {}'.format(at))
            for ai in ais:
                ai = db.get_analysis_uuid(ai.uuid)
                db.add_analysis_group_set(group, ai, analysis_type=at)

    def append_unknown_analyses(self, ans):
        pane = self.unknowns_pane
        if pane:
            pane.items.extend(ans)

    def replace_unkonwn_analyses(self, ans):
        pane = self.unknowns_pane
        if pane:
            pane.items = ans

    def find_associated_analyses(self, found=None, use_cache=True, progress=None):

        if self.active_editor:
            unks = self.active_editor.analyses

            key = lambda x: x.labnumber
            unks = sorted(unks, key=key)

            db = self.manager.db
            with db.session_ctx():
                tans = []
                if found is None:
                    uuids = []
                else:
                    uuids = found

                ngroups = len(list(groupby(unks, key=key)))
                if progress is None:
                    progress = self.manager.open_progress(ngroups + 1)
                else:
                    progress.increase_max(ngroups + 1)

                for ln, ais in groupby(unks, key=key):
                    msg = 'find associated analyses for labnumber {}'.format(ln)
                    self.debug(msg)
                    progress.change_message(msg)

                    ais = list(ais)
                    ts = [get_datetime(ai.timestamp) for ai in ais]
                    ref = ais[0]
                    ms = ref.mass_spectrometer
                    ed = ref.extract_device
                    self.debug("{} {}".format(ms, ed))
                    for atype in ('blank_unknown', 'blank_air', 'blank_cocktail',
                                  'air', 'cocktail'):
                        for i in range(10):
                            td = timedelta(hours=6 * (i + 1))
                            lpost, hpost = min(ts) - td, max(ts) + td

                            ans = db.get_date_range_analyses(lpost, hpost,
                                                             atype=atype,
                                                             spectrometer=ms)

                            if ans:
                                self.debug('{} {} to {}. nanalyses={}'.format(atype, lpost, hpost, len(ans)))
                                ans = [ai for ai in ans if ai.uuid not in uuids]
                                self.debug('new ans {}'.format(len(ans)))
                                if ans:
                                    tans.extend(ans)
                                    uuids.extend([ai.uuid for ai in ans])
                                break

                progress.soft_close()

                self.active_editor.set_items(tans, is_append=True,
                                             use_cache=use_cache, progress=progress)
                return uuids

    def _get_editor_by_uuid(self, uuid):
        return next((editor for editor in self.editor_area.editors
                     if isinstance(editor, RecallEditor) and
                        editor.model and editor.model.uuid == uuid), None)

    def recall(self, records):
        """
            if analysis is already open activate the editor
            otherwise open a new editor
        """
        self.debug('recalling records {}'.format(records))

        if not hasattr(records, '__iter__'):
            records = [records, ]

        editor = None
        #check if record already is open
        for r in records:
            editor = self._get_editor_by_uuid(r.uuid)
            if editor:
                records.remove(r)

        #activate editor if open
        if editor:
            self.activate_editor(editor)

        if records:
            ans = self.manager.make_analyses(records,
                                             unpack=True,
                                             calculate_age=True,
                                             load_changes=True)

            if ans:
                for rec in ans:
                    editor = RecallEditor(analysis_view=rec.analysis_view,
                                          model=rec)
                    self.editor_area.add_editor(editor)

                ed = self.editor_area.editors[-1]
                self.editor_area.activate_editor(ed)

    def new_ic_factor(self):
        from pychron.processing.tasks.detector_calibration.intercalibration_factor_editor import \
            IntercalibrationFactorEditor

        editor = IntercalibrationFactorEditor(name='ICFactor {:03n}'.format(self.ic_factor_editor_count),
                                              processor=self.manager)
        self._open_editor(editor)
        self.ic_factor_editor_count += 1

    def save_as(self):
        self.save()

    def save(self):
        self.warning_dialog('Please use "Data -> Database Save" to save changes to the database')

    def save_to_db(self):
        db = self.manager.db
        with db.session_ctx():
            self._save_to_db()
        self.db_save_info()

    def save_pdf_figure(self):
        if self.active_editor:

            from chaco.pdf_graphics_context import PdfPlotGraphicsContext

            p = self.save_file_dialog(ext='.pdf')
            if p:
                gc = PdfPlotGraphicsContext(filename=p)
                #pc.do_layout(force=True)
                # pc.use_backbuffer=False
                comp = self.active_editor.component
                if not issubclass(type(comp), Component):
                    comp = comp.plotcontainer
                gc.render_component(comp, valign='center')
                gc.save()

    def set_tag(self, tag=None, items=None, use_filter=True):
        """
            set tag for either
            analyses selected in unknowns pane
            or
            analyses selected in figure e.g temp_status!=0

        """
        if items is None:
            items = self._get_analyses_to_tag()

        if not items:
            self.warning_dialog('No analyses selected to Tag')
        else:
            db = self.manager.db
            name = None
            if tag is None:
                a = self._get_tagname(items)
                if a:
                    tag, items, use_filter = a
                    if tag:
                        name = tag.name
            else:
                name = tag.name

            if name and items:
                with db.session_ctx():
                    for it in items:
                        self.debug('setting {} tag= {}'.format(it.record_id, name))

                        ma = db.get_analysis_uuid(it.uuid)
                        ma.tag = name
                        it.set_tag(tag)

                if use_filter:
                    self.active_editor.filter_invalid_analyses(items)

                self.analysis_table.refresh_needed = True
                if self.unknowns_pane:
                    self.unknowns_pane.refresh_needed = True
                self._set_tag_hook()

    def prepare_destroy(self):
        if self.unknowns_pane:
            self.unknowns_pane.dump()

        super(AnalysisEditTask, self).prepare_destroy()

    def create_dock_panes(self):

        self.unknowns_pane = self._create_unknowns_pane()

        #         self.controls_pane = ControlsPane()
        self.plot_editor_pane = PlotEditorPane()
        panes = [
            self.unknowns_pane,
            #                 self.controls_pane,
            self.plot_editor_pane,
            #                self.results_pane,
            self._create_browser_pane()
        ]
        cp = self._create_control_pane()
        if cp:
            self.controls_pane = cp
            panes.append(cp)

        return panes

    def _create_control_pane(self):
        return ControlsPane()

    def _create_unknowns_pane(self):
        up = self.unknowns_pane_klass(adapter_klass=self.unknowns_adapter)
        up.load()
        return up

    def _get_tagname(self, items):
        from pychron.processing.tasks.analysis_edit.tags import TagTableView

        tv = self._tag_table_view
        if not tv:
            tv = TagTableView()

        db = self.manager.db
        with db.session_ctx():
            tv.items = items
            # tv = TagTableView(items=items)
            tv.table.db = db
            tv.table.load()

        info = tv.edit_traits()
        if info.result:
            tag = tv.selected
            self._tag_table_view = tv
            return tag, tv.items, tv.use_filter

    def _open_ideogram_editor(self, ans, name, task=None):
        _id = 'pychron.processing.figures'
        task = self._open_external_task(_id)
        task.new_ideogram(ans=ans, name=name)
        return task

    def _save_to_db(self):
        if self.active_editor:
            if hasattr(self.active_editor, 'save'):
                self.active_editor.save()

    def _set_previous_selection(self, pane, new):
        if new and new.name != 'Previous Selection':
            db = self.manager.db
            with db.session_ctx():
                lns = set([si.labnumber for si in new.analysis_ids])
                ids = [si.uuid for si in new.analysis_ids]
                if ids:
                    def f(t, t2):
                        return t2.identifier.in_(lns), t.uuid.in_(ids)

                    ans = db.get_analyses(uuid=f)
                    func = self._record_view_factory
                    ans = [func(si) for si in ans]

                    for ti in new.analysis_ids:
                        a = next((ai for ai in ans if ai.uuid == ti.uuid), None)
                        if a:
                            a.trait_set(group_id=ti.group_id, graph_id=ti.graph_id)

                    pane.items = ans

    def _save_file(self, path):
        if self.active_editor:
            self.active_editor.save_file(path)
            return True

    def _dclicked_analysis_group_hook(self, unks, b):
        pass

    #===============================================================================
    # handlers
    #===============================================================================
    def _dclicked_analysis_group_changed(self):
        if self.active_editor:
            if self.selected_analysis_groups:
                g = self.selected_analysis_groups[0]
                db = self.manager.db

                with db.session_ctx():
                    dbg = db.get_analysis_group(g.id, key='id')
                    unks, b = partition(dbg.analyses, lambda x: x.analysis_type.name == 'unknown')
                    self.active_editor.set_items([ai.analysis for ai in unks])
                    self._dclicked_analysis_group_hook(unks, b)

    def _dclicked_sample_changed(self):
        if self.unknowns_pane:
            self.debug('Dumping UnknownsPane selection')
            self.unknowns_pane.dump_selection()
            self.unknowns_pane.load_previous_selections()

        super(AnalysisEditTask, self)._dclicked_sample_changed()

    def _active_editor_changed(self):
        if self.active_editor:
            if self.controls_pane:
                tool = None
                if hasattr(self.active_editor, 'tool'):
                    tool = self.active_editor.tool

                self.controls_pane.tool = tool
            if self.unknowns_pane:
                if hasattr(self.active_editor, 'analyses'):
                    self.unknowns_pane.items = self.active_editor.analyses

    @on_trait_change('active_editor:save_event')
    def _handle_save_event(self):
        self.save_to_db()

    @on_trait_change('active_editor:component_changed')
    def _update_component(self):
        if self.plot_editor_pane:
            self.plot_editor_pane.component = self.active_editor.component
            if hasattr(self.active_editor, 'plotter_options_manager'):
                opt = self.active_editor.plotter_options_manager.plotter_options
                index_attr = opt.index_attr
                self.plot_editor_pane.index_attr = index_attr

    @on_trait_change('unknowns_pane:[items, update_needed, dclicked, refresh_editor_needed]')
    def _update_unknowns_runs(self, obj, name, old, new):
        if name == 'dclicked':
            if new:
                if isinstance(new.item, (IsotopeRecordView, Analysis)):
                    self._recall_item(new.item)
        elif name == 'refresh_editor_needed':
            self.active_editor.rebuild()
        else:
            # required for drag and drop. prevents excessive updates.
            if not obj.no_update:
                if self.active_editor:
                    self.active_editor.set_items(self.unknowns_pane.items)

                if self.plot_editor_pane:
                    self.plot_editor_pane.analyses = self.unknowns_pane.items

    @on_trait_change('plot_editor_pane:current_editor')
    def _update_current_plot_editor(self, obj, name, new):
        if new:
            if not obj.suppress_pane_change:
                self._show_pane(self.plot_editor_pane)

    @on_trait_change('analysis_table:dclicked')
    def _dclicked_analysis_changed(self, obj, name, old, new):
        if new:
            self._recall_item(new.item)

    def _recall_item(self, item):
        if not self.external_recall_window:
            self.recall(item)
        else:
            self._open_external_recall_editor(item)

    def _open_external_recall_editor(self, sel):
        tid = 'pychron.recall'
        app = self.window.application

        win, task, is_open = app.get_open_task(tid)

        if is_open:
            win.activate()
        else:
            win.open()

        task.recall(sel)

        task.load_projects()

        #print self.selected_project, 'ffff'
        task.set_projects(self.oprojects, self.selected_projects)
        task.set_samples(self.osamples, self.selected_samples)

    @on_trait_change('unknowns_pane:previous_selection')
    def _update_up_previous_selection(self, obj, name, old, new):
        self._set_previous_selection(obj, new)

    @on_trait_change('unknowns_pane:[append_button, replace_button]')
    def _append_unknowns(self, obj, name, old, new):
        is_append = name == 'append_button'

        if self.active_editor:
            unks = None
            if is_append:
                unks = self.active_editor.analyses

            s = self._get_selected_analyses(unks)
            if s:
                self.active_editor.set_items(s, is_append)

                self._add_unknowns_hook()

    def _add_unknowns_hook(self, *args, **kw):
        pass

    @on_trait_change('active_editor:analyses')
    def _ac_unknowns_changed(self):
        self.unknowns_pane._no_update = True
        self.unknowns_pane.trait_set(items=self.active_editor.analyses, trait_change_notify=True)
        self.unknowns_pane._no_update = False
        # self.unknowns_pane.trait_set(items=self.active_editor.analyses, trait_change_notify=False)

    @on_trait_change('active_editor:recall_event')
    def _handle_recall(self, new):
        self._recall_item(new)

    @on_trait_change('active_editor:tag_event')
    def _handle_tag(self, new):
        self.set_tag(items=new)

    @on_trait_change('active_editor:invalid_event')
    def _handle_invalid(self, new):
        self.set_tag(tag=Tag(name='invalid'),
                     items=new)

    #@on_trait_change('data_selector:selector:key_pressed')
    #def _key_press(self, obj, name, old, new):
    #    '''
    #        use 'u' to add selected analyses to unknowns pane
    #    '''
    #
    #    if new:
    #        s = self._get_selected_analyses()
    #        if s:
    #
    #            c = new.text
    #            if c == 'u':
    #                self.active_editor.unknowns.extend(s)
    #            elif c == 'U':
    #                self.active_editor.unknowns = s
    #            else:
    #                self._handle_key_pressed(c)
    #
    #def _handle_key_pressed(self, c):
    #    pass

    def _do_easy(self, func):
        ep = EasyParser()
        db = self.manager.db

        prog = self.manager.open_progress(n=10, close_at_end=False)
        with db.session_ctx() as sess:
            ok = func(db, ep, prog)
            if not ok:
                sess.rollback()

        prog.close()
        if ok:
            self.db_save_info()

    def _get_analyses_to_group(self):
        items = None
        if self.unknowns_pane:
            items = self.unknowns_pane.selected

        if not items:
            if self.unknowns_pane:
                items = self.unknowns_pane.items
        if not items:
            items = self.analysis_table.selected

        if items:
            return ((items, 'unknown'),)  #unknown analysis type

    def _get_analyses_to_tag(self):
        items = None

        if self.unknowns_pane:
            items = [i for i in self.unknowns_pane.items
                     if i.is_temp_omitted()]
            self.debug('Temp omitted analyses {}'.format(len(items)))
            if not items:
                items = self.unknowns_pane.selected

        if not items:
            items = self.analysis_table.selected

        return items

    def _set_tag_hook(self):
        pass

#===============================================================================
#
#===============================================================================
#    @on_trait_change('unknowns_pane:[+button]')
#    def _update_unknowns(self, name, new):
#        print name, new
#        '''
#            get selected analyses and append/replace to unknowns_pane.items
#        '''
#        sel = None
#        if sel:
#            if name == 'replace_button':
#                self.unknowns_pane.items = sel
#            else:
#                self.unknowns_pane.items.extend(sel)

#    @on_trait_change('references_pane:[+button]')
#    def _update_items(self, name, new):
#        print name, new
#        sel = None
#        if sel:
#            if name == 'replace_button':
#                self.references_pane.items = sel
#            else:
#                self.references_pane.items.extend(sel)


#============= EOF =============================================
