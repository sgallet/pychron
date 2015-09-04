# ===============================================================================
# Copyright 2015 Jake Ross
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
import hashlib
import os

from pychron.core.ui import set_qt

set_qt()

# ============= enthought library imports =======================
from pyface.action.menu_manager import MenuManager
from traitsui.menu import Action
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import HasTraits, Str, Instance, Event, Bool, List, Enum, Any
from traitsui.api import View, UItem, VGroup, TreeNode, Handler, HGroup, TextEditor

# ============= standard library imports ========================
import yaml
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths
from pychron.envisage.resources import icon
from pychron.core.helpers.strtools import to_bool
from pychron.core.ui.tree_editor import TreeEditor


class AdditionTreeNode(TreeNode):
    def get_icon(self, obj, is_expanded):
        return icon('tick' if obj.enabled else 'cancel')


class TETreeNode(TreeNode):
    def get_icon(self, obj, is_expanded):
        return icon('package-green')


class ViewModel(HasTraits):
    otask_extensions = List
    task_extensions = List
    enabled = True
    # pychron.update.check_for_updates',

    def filter(self, new):
        if new:
            exs = []
            for te in self.otask_extensions:
                adds = []
                for a in te.additions:
                    if a.name.lower().startswith(new):
                        adds.append(a)
                if adds:
                    tt = te.clone_traits()
                    tt.additions = adds
                    exs.append(tt)
        else:
            exs = self.otask_extensions[:]

        self.task_extensions = exs

    def set_states(self, modename):
        if modename == 'simple':
            enables = []
            p = paths.simple_ui_file
            try:
                with open(p, 'r') as rfile:
                    enables = yaml.load(rfile)
            except BaseException, e:
                print 'ViewModel.set states', e
        elif modename == 'advanced':
            enables = None
        else:
            enables = None

        if enables is None:
            # enable all
            for t in self.task_extensions:
                t.enable_all(True)
        else:
            # disable all
            for t in self.task_extensions:
                t.enable_all(False)

            # enable specified ids
            for ei in enables:
                te = next((a for t in self.task_extensions
                           for a in t.additions if a.model.id == ei), None)
                if not te:
                    pass
                    # print 'aaaaaasdfsdf', ei
                else:
                    te.enabled = True

    def load(self):
        p = paths.task_extensions_file
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                yl = yaml.load(rfile)
                for te in self.task_extensions:
                    yd = next((d for d in yl if d['plugin_id'] == te.id), None)
                    if yd:
                        for ai in yd['actions']:
                            action, enabled = ai.split(',')
                            tt = next((ta for ta in te.additions if ta.model.id == action), None)
                            if tt:
                                tt.enabled = to_bool(enabled)

    def dump(self):
        p = paths.task_extensions_file
        obj = [te.dump() for te in self.task_extensions]

        with open(p, 'w') as wfile:
            yaml.dump(obj, wfile)

    def get_te_model(self, tid):
        return next((te for te in self.task_extensions if te.id == tid), None)

    def calc_hash(self):
        h = hashlib.md5()
        for te in self.task_extensions:
            for a in te.additions:
                h.update('{}{}'.format(a.model.id, a.enabled))
        return h.hexdigest()


class TaskExtensionModel(HasTraits):
    additions = List
    id = Str
    all_enabled = Bool
    enabled = True
    task_id = Str

    def dump(self):
        return {'plugin_id': self.id,
                'task_id': self.task_id,
                'actions': ['{}, {}'.format(a.model.id, a.enabled) for a in self.additions]}

    def enable_all(self, v):
        for a in self.additions:
            a.enabled = v


class AdditionModel(HasTraits):
    model = SchemaAddition
    name = Str
    enabled = Bool


class EEHandler(Handler):
    def set_enabled(self, info, obj):
        for si in info.object.selected:
            si.enabled = True
        info.object.update()

    def set_disabled(self, info, obj):
        for si in info.object.selected:
            si.enabled = False
        info.object.update()

    def set_all_enabled(self, info, obj):
        self._set_all(obj, True)
        info.object.update()

    def set_all_disabled(self, info, obj):
        self._set_all(obj, False)
        info.object.update()

    def _set_all(self, te, v):
        te.enable_all(v)
        te.all_enabled = v


class EditExtensionsView(HasTraits):
    view_model = Instance(ViewModel, ())
    predefined = Enum('', 'Simple', 'Advanced')
    selected = Any
    filter_value = Str
    description = Str

    collapse_all = Event
    expand_all = Event

    dclicked = Event
    refresh_all_needed = Event
    refresh_needed = Event

    _predefined_hash = None

    def update(self):
        self.refresh_all_needed = True
        if self._predefined_hash != self.view_model.calc_hash():
            self.predefined = ''

    def load(self):
        self.view_model.load()
        if os.path.isfile(paths.edit_ui_defaults):
            with open(paths.edit_ui_defaults, 'r') as rfile:
                try:
                    d = yaml.load(rfile)
                    self.trait_set(**d)
                except BaseException, e:
                    print 'exception', e

    def dump(self):
        self.view_model.dump()
        self._dump()

    def add_additions(self, tid, task_id, name, a):
        print tid, task_id
        adds = []
        for ai in a:
            d = ''
            if hasattr(ai.factory, 'ddescription'):
                d = ai.factory.ddescription

            adds.append(AdditionModel(model=ai,
                                      name=ai.factory.dname,
                                      description=d))
        te = self.view_model.get_te_model(tid)
        if te is None:
            te = TaskExtensionModel(name=name,
                                    task_id=task_id,
                                    id=tid,
                                    additions=adds)
            self.view_model.otask_extensions.append(te)
            self.view_model.task_extensions.append(te)
        else:
            ids = [a.model.id for a in te.additions]
            adds = [ai for ai in adds if ai.model.id not in ids]
            te.additions.extend(adds)

    # private
    def _dump(self):
        if self._predefined_hash != self.view_model.calc_hash():
            self.predefined = ''

        with open(paths.edit_ui_defaults, 'w') as wfile:
            d = {k: getattr(self, k) for k in ('predefined',)}
            yaml.dump(d, wfile)

    # handlers
    # def _collapse_button_fired(self):
    #     print 'collapse'
    #     self.collapse_all = True

    # def _expand_button_fired(self):
    #     self.collapse_all = True
    #     print 'expand'

    def _filter_value_changed(self, new):
        self.view_model.filter(new)
        self.refresh_needed = True

    def _predefined_changed(self, new):
        if new:
            self.view_model.set_states(new.lower())

            self._predefined_hash = self.view_model.calc_hash()
            self.refresh_all_needed = True

    def _dclicked_fired(self):
        s = self.selected
        s.enabled = not s.enabled
        self.update()

    def _selected_changed(self, new):
        print new
        try:
            self.description = new.description
        except AttributeError:
            self.description = ''


def edit_task_extensions(ts):
    e = EditExtensionsView()
    for args in ts:
        e.add_additions(*args)
    e.load()

    nodes = [TreeNode(node_for=[ViewModel],
                      icon_open='',
                      children='task_extensions'),
             TETreeNode(node_for=[TaskExtensionModel],
                        auto_open=False,
                        children='additions',
                        label='name',
                        menu=MenuManager(Action(name='Enable All',
                                                visible_when='not object.all_enabled',
                                                action='set_all_enabled'),
                                         Action(name='Disable All',
                                                visible_when='object.all_enabled',
                                                action='set_all_disabled'))),
             AdditionTreeNode(node_for=[AdditionModel],
                              label='name',
                              menu=MenuManager(Action(name='Enable',
                                                      action='set_enabled',
                                                      visible_when='not object.enabled'),
                                               Action(name='Disable',
                                                      visible_when='object.enabled',
                                                      action='set_disabled')))]
    tgrp = VGroup(UItem('predefined', tooltip='List of Predefined UI configurations'),
                  UItem('filter_value',
                        tooltip='Filter items by name. Show only items where NAME starts with the specified value'),

                  HGroup(icon_button_editor('collapse_all', 'collapse'),
                         icon_button_editor('expand_all', 'collapse'), ),

                  UItem('view_model',
                        height=-400,
                        editor=TreeEditor(nodes=nodes,
                                          # selection_mode='extended',
                                          hide_root=True,
                                          selected='selected',
                                          dclick='dclicked',
                                          show_disabled=True,
                                          collapse_all='collapse_all',
                                          expand_all='expand_all',
                                          refresh='refresh_needed',
                                          refresh_all_icons='refresh_all_needed',
                                          editable=False)))
    dgrp = VGroup(UItem('description',
                        style='custom',
                        # height=-100,
                        editor=TextEditor(read_only=True)),
                  show_border=True, label='Description')

    av = View(VGroup(tgrp, dgrp),
              title='Edit UI',
              width=500,
              height=700,
              resizable=True,
              handler=EEHandler(),
              buttons=['OK', 'Cancel'],
              kind='livemodal')

    # info = e.configure_traits(view=AView)
    info = e.edit_traits(view=av)
    if info.result:
        e.dump()
        return confirm(None, 'Restart?') == YES


if __name__ == '__main__':
    from traits.api import Button
    from pychron.processing.tasks.actions.processing_actions import RecallAction
    from pychron.updater.tasks.actions import CheckForUpdatesAction, ManageBranchAction

    class Demo(HasTraits):
        test = Button
        traits_view = View('test')

        def _test_fired(self):
            a = [('pychron.update', '', 'Update', [SchemaAddition(id='pychron.update.check_for_updates',
                                                                  factory=CheckForUpdatesAction),
                                                   SchemaAddition(id='pychron.update.manage_branch',
                                                                  factory=ManageBranchAction)]),
                 ('pychron.recall', '', 'Recall', [SchemaAddition(id='pychron.recall',
                                                                  factory=RecallAction),
                                                   SchemaAddition(id='pychron.update.manage_branch',
                                                                  factory=ManageBranchAction)])]
            edit_task_extensions(a)

    d = Demo()
    d.configure_traits()
# ============= EOF =============================================
