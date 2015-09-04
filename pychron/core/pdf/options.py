# ===============================================================================
# Copyright 2013 Jake Ross
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

# ============= enthought library imports =======================
import os

from traits.api import HasTraits, Str, Bool, Color, Enum, \
    Button, Float, TraitError, Property, Int
from traitsui.api import View, Item, UItem, HGroup, Group, VGroup


# ============= standard library imports ========================
# ============= local library imports  ==========================
import yaml
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.globals import globalv
from pychron.paths import paths


class BasePDFOptions(HasTraits):
    orientation = Enum('landscape', 'portrait')
    left_margin = Float(1.5)
    right_margin = Float(1)
    top_margin = Float(1)
    bottom_margin = Float(1)
    show_page_numbers = Bool(False)
    use_alternating_background = Bool
    alternating_background = Color

    persistence_path = Property
    _persistence_name = 'base_pdf_options'

    def __init__(self, *args, **kw):
        super(BasePDFOptions, self).__init__(*args, **kw)
        self.load_yaml()

    def _get_persistence_path(self):
        return os.path.join(paths.hidden_dir, '{}.{}'.format(self._persistence_name, globalv.username))

    def dump_yaml(self):
        p = self.persistence_path
        with open(p, 'w') as wfile:
            yaml.dump(self.get_dump_dict(), wfile)

    def _get_dump_attrs(self):
        return ('orientation', 'left_margin', 'right_margin',
                'top_margin', 'bottom_margin', 'show_page_numbers',
                'use_alternating_background')

    def get_dump_dict(self):
        dd = {k: getattr(self, k) for k in self._get_dump_attrs()}
        # d = dict(orientation=self.orientation,
        # left_margin=self.left_margin,
        # right_margin=self.right_margin,
        # top_margin=self.top_margin,
        # bottom_margin=self.bottom_margin)
        dd['alternating_background'] = self.get_alternating_background()

        return dd

    def set_alternating_background(self, t):
        self.alternating_background = tuple(map(lambda x: int(x * 255), t))

    def get_alternating_background(self):
        t = self.alternating_background.toTuple()[:3]
        return map(lambda x: x / 255., t)

    def get_load_dict(self):
        d = {}
        p = self.persistence_path
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                try:
                    d = yaml.load(rfile)
                except yaml.YAMLError:
                    pass
        return d

    def load_yaml(self):
        d = self.get_load_dict()
        for k, v in d.iteritems():
            try:
                setattr(self, k, v)
            except TraitError:
                pass

        ab = d.get('use_alternating_background', False)
        if ab:
            self.set_alternating_background(d.get('alternating_background',
                                                  (0.7, 0.7, 0.7)))
        self._load_yaml_hook(d)

    def _load_yaml_hook(self, d):
        pass


class PDFTableOptions(BasePDFOptions):
    title = Str
    auto_title = Bool


    # show_page_numbers = Bool
    default_row_height = Float(0.22)
    default_header_height = Float(0.22)
    options_button = Button
    age_nsigma = Enum(1, 2, 3)
    kca_nsigma = Enum(1, 2, 3)
    link_sigmas = Bool(True)

    age_units = Enum('Ma', 'ka', 'Ga', 'a')
    kca_sig_figs = Int
    age_sig_figs = Int

    _persistence_name = 'table_pdf_options'

    def _load_yaml_hook(self, d):

        self.age_nsigma = d.get('age_nsigma', 2)
        self.kca_nsigma = d.get('kca_nsigma', 2)
        self.link_sigmas = d.get('link_sigmas', True)

        self.age_sig_figs = d.get('age_sig_figs', 3)

        self.kca_sig_figs = d.get('kca_sig_figs', 3)

        self.age_units = d.get('age_units', 'Ma')

    def _get_dump_attrs(self):
        return ('auto_title',
                'age_nsigma',
                'kca_nsigma',
                'link_sigmas',
                'age_sig_figs',
                'kca_sig_figs',
                'age_units')

    def get_dump_dict(self):
        d = super(PDFTableOptions, self).get_dump_dict()
        d.update(dict(title=str(self.title),
                      ))

        return d

    def _options_button_fired(self):
        if self.edit_traits(view='advanced_view', kind='livemodal'):
            self.dump_yaml()

    def _age_nsigma_changed(self):
        if self.link_sigmas:
            self.kca_nsigma = self.age_nsigma

    def _kca_nsigma_changed(self):
        if self.link_sigmas:
            self.age_nsigma = self.kca_nsigma

    def _link_sigmas_changed(self):
        if self.link_sigmas:
            self.kca_nsigma = self.age_nsigma

    def traits_view(self):
        v = View(HGroup(Item('auto_title'),
                        UItem('title', enabled_when='not auto_title'),
                        icon_button_editor('options_button', 'cog')))
        return v

    def advanced_view(self):
        table_grp = Group(Item('use_alternating_background'),
                          Item('alternating_background'),
                          label='Table')

        layout_grp = Group(Item('orientation'),
                           Item('left_margin'),
                           Item('right_margin'),
                           Item('top_margin'),
                           Item('bottom_margin'),
                           label='layout')

        data_grp = Group(Item('link_sigmas', label='Link'),
                         Item('age_nsigma', label='Age NSigma'),
                         Item('kca_nsigma', label='K/CA NSigma'),
                         Item('age_units'),
                         VGroup(
                             HGroup(Item('age_sig_figs', label='Age')),
                             HGroup(Item('kca_sig_figs', label='K/Ca')),
                             label='Sig Figs'),
                         label='Data')
        v = View(
            layout_grp,
            table_grp,
            data_grp,
            title='PDF Options',
            buttons=['OK', 'Cancel', 'Revert'])
        return v
        # ============= EOF =============================================