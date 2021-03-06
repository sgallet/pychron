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
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from traits.api import HasTraits, Str, List, Instance, Any, Button, Date, Bool
from traitsui.api import View, Item, UItem, HGroup, TableEditor, \
    Handler, VGroup, TabularEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.loggable import Loggable


class ItemAdapter(TabularAdapter):
    columns = [('Run ID', 'record_id'),
               ('Sample', 'sample'),
               ('Tag', 'tag')]
    font = 'arial 10'


class Tag(HasTraits):
    name = Str
    user = Str
    date = Date
    omit_ideo = Bool
    omit_spec = Bool
    omit_iso = Bool
    omit_series = Bool


class TagTable(HasTraits):
    tags = List
    db = Any

    def load(self):
        db = self.db
        with db.session_ctx():
            dbtags = db.get_tags()

            #make invalid and ok first in tag list

            invalid_tag = next((t for t in dbtags
                                if t.name == 'invalid'), None)
            ok_tag = next((t for t in dbtags
                           if t.name == 'ok'), None)
            f = []
            if invalid_tag:
                dbtags.remove(invalid_tag)
                f.append(invalid_tag)

            if ok_tag:
                dbtags.remove(ok_tag)
                f.append(ok_tag)

            tags = f + dbtags

            ts = [Tag(name=di.name,
                      user=di.user,
                      date=di.create_date,
                      omit_ideo=di.omit_ideo or False,
                      omit_iso=di.omit_iso or False,
                      omit_spec=di.omit_spec or False,
                      omit_series=di.omit_series or False)
                  for di in tags]

            self.tags = ts

    def _add_tag(self, tag):
        name, user = tag.name, tag.user
        db = self.db
        with db.session_ctx():
            return db.add_tag(name=name, user=user,
                              omit_ideo=tag.omit_ideo,
                              omit_spec=tag.omit_spec,
                              omit_iso=tag.omit_iso,
                              omit_series=tag.omit_series)

    def add_tag(self, tag):
        self._add_tag(tag)
        self.load()

    def delete_tag(self, tag):
        if isinstance(tag, str):
            tag = next((ta for ta in self.tags if ta.name == tag), None)

        if tag:
            self.tags.remove(tag)
            db = self.db
            with db.session_ctx():
                db.delete_tag(tag.name)

    def save(self):
        db = self.db
        with db.session_ctx():
            for ti in self.tags:
                dbtag = db.get_tag(ti.name)
                if dbtag is None:
                    dbtag = self._add_tag(ti)

                for a in ('ideo', 'spec', 'iso', 'series'):
                    a = 'omit_{}'.format(a)
                    setattr(dbtag, a, getattr(ti, a))


#class TagAdapter(TabularAdapter):
#    columns = [('Name', 'name'), ('User', 'user'),
#               ('Date', 'date')
#               ]
class TagTableViewHandler(Handler):
    def closed(self, info, isok):
        if isok:
            info.object.save()


class TagTableView(Loggable):
    table = Instance(TagTable, ())
    add_tag_button = Button
    delete_tag_button = Button
    save_button = Button

    selected = Any
    items = List
    use_filter = Bool(True)

    def save(self):
        self.table.save()

    def _save_button_fired(self):
        self.save()
        self.information_dialog('Changes saved to database')

    def _add_tag_button_fired(self):
        n = Tag()
        tag_view = View(
            VGroup(
                HGroup(Item('name'),
                       #Label('optional'),
                       Item('user')),
                HGroup(
                    Item('omit_ideo',
                         label='Ideogram'),
                    Item('omit_spec',
                         label='Spectrum'),
                    Item('omit_iso',
                         label='Isochron'),
                    Item('omit_series',
                         label='Series'),
                    show_border=True,
                    label='Omit'
                ),
            ),
            buttons=['OK', 'Cancel'],
            title='Add Tag'
        )
        info = n.edit_traits(kind='livemodal', view=tag_view)
        if info.result:
            self.table.add_tag(n)

    def _delete_tag_button_fired(self):
        s = self.selected
        if s:
            if not isinstance(s, list):
                s = (s,)
            for si in s:
                self.table.delete_tag(si)

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                ObjectColumn(name='user', editable=False),
                CheckboxColumn(name='omit_ideo'),
                CheckboxColumn(name='omit_spec'),
                CheckboxColumn(name='omit_iso'),
                CheckboxColumn(name='omit_series')]

        editor = TableEditor(columns=cols,
                             selected='selected',
                             sortable=False,
        )

        v = View(UItem('object.table.tags',
                       editor=editor),
                 HGroup(
                     icon_button_editor('add_tag_button', 'add', tooltip='Add a tag'),
                     icon_button_editor('delete_tag_button', 'delete', tooltip='Delete selected tags'),
                     icon_button_editor('save_button', 'database_save',
                                        tooltip='Save changes from the "Tag" table to the database')),
                 UItem('items', editor=TabularEditor(adapter=ItemAdapter(),
                                                     multi_select=True,
                                                     operations=['delete'])),
                 HGroup(Item('use_filter', label='Remove "Invalid" analyses from figure')),

                 resizable=True,
                 width=500,
                 height=400,
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 handler=TagTableViewHandler,
                 title='Tags')

        return v


if __name__ == '__main__':
    t = TagTableView()
    t.table.tags = [Tag(name='foo') for i in range(10)]
    t.configure_traits()
#============= EOF =============================================
