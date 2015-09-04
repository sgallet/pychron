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

from traits.api import Str, Property, Enum, Button, List, Int, Any, on_trait_change, Instance, Bool
from traitsui.api import View, Item, HGroup, VGroup, Group, \
    EnumEditor, TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from kiva.fonttools import str_to_font
from enable.markers import marker_names
# ============= standard library imports ========================
from itertools import groupby
# ============= local library imports  ==========================
from pychron.core.ui.table_editor import myTableEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.processing.plotters.options.base import FigurePlotterOptions
from pychron.processing.plotters.options.option import AuxPlotOptions
from pychron.pychron_constants import ALPHAS

FONTS = ['Helvetica', ]  # 'Courier','Times-Roman']#['modern', 'arial']
SIZES = [10, 6, 8, 9, 10, 11, 12, 14, 15, 18, 24, 36]


def _table_column(klass, *args, **kw):
    kw['text_font'] = 'arial 10'
    return klass(*args, **kw)


def object_column(*args, **kw):
    return _table_column(ObjectColumn, *args, **kw)


def checkbox_column(*args, **kw):
    return _table_column(CheckboxColumn, *args, **kw)


class PlotterOptions(FigurePlotterOptions):
    title = Str
    edit_title_format = Button
    title_formatter = Str
    title_attribute_keys = List
    title_delimiter = Str(',')
    title_leading_text = Str
    title_trailing_text = Str
    # auto_generate_title = Bool
    # data_type = Str('database')

    xtick_font = Property
    xtick_font_size = Enum(*SIZES)
    xtick_font_name = Enum(*FONTS)
    xtick_in = Int(1)
    xtick_out = Int(5)

    xtitle_font = Property
    xtitle_font_size = Enum(*SIZES)
    xtitle_font_name = Enum(*FONTS)

    ytick_font = Property
    ytick_font_size = Enum(*SIZES)
    ytick_font_name = Enum(*FONTS)
    ytick_in = Int(1)
    ytick_out = Int(5)

    ytitle_font = Property
    ytitle_font_size = Enum(*SIZES)
    ytitle_font_name = Enum(*FONTS)

    x_filter_str = Str

    @on_trait_change('aux_plots:name')
    def _handle_name_change(self, obj, name, old, new):
        print obj, name, old, new
        obj.clear_ylimits()


    def _edit_title_format_fired(self):
        from pychron.processing.label_maker import TitleTemplater, TitleTemplateView

        tm = TitleTemplater(label=self.title,
                            delimiter=self.title_delimiter,
                            leading_text=self.title_leading_text,
                            trailing_text=self.title_trailing_text)

        tv = TitleTemplateView(model=tm)
        info = tv.edit_traits()
        if info.result:
            self.title_formatter = tm.formatter
            self.title_attribute_keys = tm.attribute_keys
            self.title_leading_text = tm.leading_text
            self.title_trailing_text = tm.trailing_text
            self.title = tm.label
            self.title_delimiter = tm.delimiter

    def generate_title(self, analyses, n):
        attrs = self.title_attribute_keys
        ts = []
        rref, ctx = None, {}
        material_map = {'Groundmass concentrate': 'GMC',
                        'Kaersutite': 'Kaer',
                        'Plagioclase': 'Plag',
                        'Sanidine': 'San'}

        for gid, ais in groupby(analyses, key=lambda x: x.group_id):
            ref = ais.next()
            d = {}
            for ai in attrs:
                if ai == 'alphacounter':
                    v = ALPHAS[n]
                elif ai == 'numericcounter':
                    v = n
                else:
                    v = getattr(ref, ai)
                    if ai == 'material':
                        try:
                            v = material_map[v]
                        except KeyError:
                            pass
                d[ai] = v

            if not rref:
                rref = ref
                ctx = d

            ts.append(self.title_formatter.format(**d))

        t = self.title_delimiter.join(ts)
        lt = self.title_leading_text
        if lt:
            if lt.lower() in ctx:
                lt = ctx[lt.lower()]
            t = '{} {}'.format(lt, t)

        tt = self.title_trailing_text
        if tt:
            if tt.lower() in ctx:
                tt = ctx[tt.lower()]
            t = '{} {}'.format(t, tt)

        return t

    def construct_plots(self, plist):
        """
            plist is a list of dictionaries
        """
        ps = [self.plot_option_klass(**pi) for pi in plist]
        self.aux_plots = ps

    def add_aux_plot(self, **kw):
        ap = self.plot_option_klass(**kw)
        self.aux_plots.append(ap)

    def _create_axis_group(self, axis, name):

        hg = HGroup(
            # Label(name.capitalize()),
            Item('{}{}_font_name'.format(axis, name), label=name.capitalize()),
            Item('{}{}_font_size'.format(axis, name), show_label=False),
            # Spring(width=125, springy=False)
        )
        return hg

    def _get_dump_attrs(self):
        attrs = super(PlotterOptions, self)._get_dump_attrs()
        attrs += ['title', 'auto_generate_title',
                  'title_formatter',
                  'title_attribute_keys',
                  'title_delimiter',
                  'title_leading_text',
                  'title_trailing_text',
                  # 'data_type',
                  'xtick_in',
                  'ytick_in',
                  'xtick_out',
                  'ytick_out',
                  'xtick_font_size',
                  'xtick_font_name',
                  'xtitle_font_size',
                  'xtitle_font_name',
                  'ytick_font_size',
                  'ytick_font_name',
                  'ytitle_font_size',
                  'ytitle_font_name',
                  'x_filter_str']

        return attrs

    def _get_change_attrs(self):
        return ['xtick_in', 'ytick_in', 'xtick_out', 'ytick_out', 'xtick_font_size', 'xtick_font_name',
                'xtitle_font_size', 'xtitle_font_name', 'ytick_font_size', 'ytick_font_name', 'ytitle_font_size',
                'ytitle_font_name', ]

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_xtick_font(self):
        return self._get_font('xtick', default_size=10)

    def _get_xtitle_font(self):
        return self._get_font('xtitle', default_size=12)

    def _get_ytick_font(self):
        return self._get_font('ytick', default_size=10)

    def _get_ytitle_font(self):
        return self._get_font('ytitle', default_size=12)

    def _get_font(self, name, default_size=10):
        xn = getattr(self, '{}_font_name'.format(name))
        xs = getattr(self, '{}_font_size'.format(name))
        if xn is None:
            xn = FONTS[0]
        if xs is None:
            xs = default_size
        return str_to_font('{} {}'.format(xn, xs))

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _xtitle_font_size_default(self):
        return 12

    def _xtick_font_size_default(self):
        return 10

    def _ytitle_font_size_default(self):
        return 12

    def _ytick_font_size_default(self):
        return 10

    def _aux_plots_default(self):
        return [self.plot_option_klass() for _ in range(5)]

    # ===============================================================================
    # views
    # ===============================================================================
    def _get_groups(self):
        pass

    def _get_axes_group(self):
        axis_grp = Group(self._get_x_axis_group(), self._get_y_axis_group(),
                         enabled_when='not formatting_options',
                         layout='tabbed', show_border=True, label='Axes')
        grid_grp = VGroup(Item('use_xgrid',
                               label='XGrid Visible'),
                          Item('use_ygrid', label='YGrid Visible'),
                          show_border=True,
                          label='Grid')
        grp = VGroup(axis_grp, grid_grp)
        return grp

    def _get_x_axis_group(self):
        v = VGroup(
            self._create_axis_group('x', 'title'),
            self._create_axis_group('x', 'tick'),

            Item('xtick_in', label='Tick In', tooltip='The number of pixels by which '
                                                      'the ticks extend into the plot area.'),
            Item('xtick_out', label='Tick Out', tooltip='The number of pixels by which '
                                                        'the ticks extend into the label area.'),
            # show_border=True,
            label='X')
        return v

    def _get_y_axis_group(self):
        v = VGroup(
            self._create_axis_group('y', 'title'),
            self._create_axis_group('y', 'tick'),
            Item('ytick_in', label='Tick In', tooltip='The number of pixels by which '
                                                      'the ticks extend into the plot area.'),
            Item('ytick_out', label='Tick Out', tooltip='The number of pixels by which '
                                                        'the ticks extend into the label area.'),
            # show_border=True,
            label='Y')
        return v

    # def _get_info_group(self):
    # return Group()
    def _get_title_group(self):
        return VGroup(HGroup(Item('auto_generate_title',
                                  tooltip='Auto generate a title based on the analysis list'),
                             icon_button_editor('edit_title_format', 'cog',
                                                enabled_when='auto_generate_title')),
                      Item('title', springy=False,
                           enabled_when='not auto_generate_title',
                           tooltip='User specified plot title'),
                      label='Title', show_border=True)

    def _get_main_group(self):
        main_grp = VGroup(self._get_aux_plots_group(),
            HGroup(Item('plot_spacing', label='Spacing',
                        tooltip='Spacing between stacked plots')),
            label='Plots')
        return main_grp

    def _get_aux_plots_group(self):
        cols = [checkbox_column(name='use', ),
                object_column(name='name',
                              width=130,
                              editor=EnumEditor(name='names')),
                object_column(name='scale'),
                object_column(name='height',
                              format_func=lambda x: str(x) if x else ''),
                checkbox_column(name='show_labels', label='Labels'),
                checkbox_column(name='x_error', label='X Err.'),
                checkbox_column(name='y_error', label='Y Err.'),
                checkbox_column(name='ytick_visible', label='Y Tick'),
                checkbox_column(name='ytitle_visible', label='Y Title'),
                # object_column(name='filter_str', label='Filter')
                ]

        v = View(VGroup(Item('name', editor=EnumEditor(name='names')),
                        Item('marker', editor=EnumEditor(values=marker_names)),
                        Item('marker_size'),
                        HGroup(Item('ymin', label='Min'),
                               Item('ymax', label='Max'),
                               show_border=True,
                               label='Y Limits'),
                        show_border=True))

        aux_plots_grp = Item('aux_plots',
                             style='custom',
                             show_label=False,
                             editor=myTableEditor(columns=cols,
                                                  sortable=False,
                                                  deletable=False,
                                                  clear_selection_on_dclicked=True,
                                                  edit_on_first_click=False,
                                                  # on_select=lambda *args: setattr(self, 'selected', True),
                                                  # selected='selected',
                                                  edit_view=v,
                                                  reorderable=False))
        return aux_plots_grp

    def traits_view(self):
        main_grp = self._get_main_group()
        bg_grp = self._get_bg_group()
        pd_grp = self._get_padding_group()
        a_grp = self._get_axes_group()
        grps = self._get_groups()
        if grps:
            a_grp = VGroup(bg_grp, pd_grp,
                           a_grp,
                           label='Appearance',
                           show_border=True)
            g = Group(main_grp,
                      a_grp,
                      # bg_grp,
                      # self._get_padding_group(),
                      layout='fold', *grps)
        else:
            g = Group(main_grp, bg_grp, pd_grp)

        v = View(VGroup(self._get_refresh_group(), g),
            scrollable=True)
        # v = View(VGroup(self._get_refresh_group(),g))
        return v

# ============= EOF =============================================
