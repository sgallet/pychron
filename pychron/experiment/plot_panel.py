# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Instance, Property, List, on_trait_change, Bool, \
    Str, CInt, Tuple, Color, HasTraits, Any, Int
from traitsui.api import View, UItem, VGroup, HGroup, spring, ListEditor
# ============= standard library imports ========================
from threading import Event
import time
# ============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.core.ui.text_table import MultiTextTableAdapter
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.graph.stacked_regression_graph import StackedRegressionGraph
from pychron.processing.analyses.view.automated_run_view import AutomatedRunAnalysisView
from pychron.processing.arar_age import ArArAge
from pychron.pychron_constants import PLUSMINUS
from pychron.loggable import Loggable

HEIGHT = 250
ERROR_WIDTH = 10
VALUE_WIDTH = 12


class SignalAdapter(MultiTextTableAdapter):
    columns = [[('Iso.', 'isotope', str, 6),
                ('Det.', 'detector', str, 5),
                ('Fit', 'fit', str, 4),
                ('Intercept', 'intercept_value', None, VALUE_WIDTH),
                (u'{}1s'.format(PLUSMINUS), 'intercept_error', None, ERROR_WIDTH),
                (u'{}%'.format(PLUSMINUS), 'intercept_error_percent', str, ERROR_WIDTH - 1),
                ('Raw(fA)', 'raw_value', None, VALUE_WIDTH),
                (u'{}1s'.format(PLUSMINUS), 'raw_error', None, ERROR_WIDTH),
                (u'{}%'.format(PLUSMINUS), 'raw_error_percent', str, ERROR_WIDTH - 1)],
               [('Iso.', 'isotope', str, 6),
                ('Det.', 'detector', str, 5),
                ('Fit', 'baseline_fit', str, 4),
                ('Baseline', 'baseline_value', None, VALUE_WIDTH),
                (u'{}1s'.format(PLUSMINUS), 'baseline_error', None, ERROR_WIDTH),
                (u'{}%'.format(PLUSMINUS), 'baseline_error_percent', str, ERROR_WIDTH - 1),
                ('Blank', 'blank_value', None, VALUE_WIDTH),
                (u'{}1s'.format(PLUSMINUS), 'blank_error', None, ERROR_WIDTH),
                (u'{}%'.format(PLUSMINUS), 'blank_error_percent', str, ERROR_WIDTH - 1)]]


class TraitsContainer(HasTraits):
    model = Any

    def trait_context(self):
        """ Use the model object for the Traits UI context, if appropriate.
        """
        if self.model:
            return {'object': self.model}
        return super(TraitsContainer, self).trait_context()


class GraphContainer(TraitsContainer):
    def traits_view(self):
        v = View(
            VGroup(
                HGroup(spring,
                       CustomLabel('plot_title',
                                   weight='bold',
                                   size=14),
                       spring),
                UItem('graphs',
                      editor=ListEditor(use_notebook=True,
                                        selected='selected_graph',
                                        page_name='.page_name'),
                      style='custom')))
        return v


class PlotPanel(Loggable):
    graph_container = Instance(GraphContainer)
    analysis_view = Instance(AutomatedRunAnalysisView, ())

    arar_age = Instance(ArArAge)

    isotope_graph = Instance(Graph, ())
    peak_center_graph = Instance(Graph, ())
    selected_graph = Any

    graphs = Tuple

    plot_title = Str

    display_counts = Property(depends_on='counts')
    counts = Int
    ncounts = Property(CInt(enter_set=True, auto_set=False),
                       depends_on='_ncounts')
    _ncounts = CInt

    ncycles = Property(CInt(enter_set=True, auto_set=False),
                       depends_on='_ncycles')
    _ncycles = CInt

    current_cycle = Str
    current_color = Color

    detectors = List

    stack_order = 'bottom_to_top'
    series_cnt = 0

    total_counts = CInt

    is_baseline = Bool(False)
    is_peak_hop = Bool(False)
    hops = List

    ratios = ['Ar40:Ar36', 'Ar40:Ar39', ]
    info_func = None

    # refresh_age = True

    def set_peak_center_graph(self, graph):
        self.peak_center_graph = graph
        self.show_graph(graph)

    def show_graph(self, g):
        invoke_in_main_thread(self.trait_set, selected_graph=g)

    def show_isotope_graph(self):
        self.show_graph(self.isotope_graph)

    def info(self, *args, **kw):
        if self.info_func:
            self.info_func(*args, **kw)
        else:
            super(PlotPanel, self).info(*args, **kw)

    def reset(self):
        self.debug('clearing graphs')
        self.isotope_graph.clear()
        self.peak_center_graph.clear()

    def create(self, dets):
        """
            dets: list of Detector instances
        """

        self.detectors = dets

        evt = Event()
        invoke_in_main_thread(self._create, evt)

        # wait here until _create finishes
        while not evt.is_set():
            time.sleep(0.05)

    def new_plot(self, **kw):
        return self._new_plot(**kw)

    def _new_plot(self, **kw):
        g = self.isotope_graph
        plot = g.new_plot(xtitle='time (s)', padding_left=70,
                          padding_right=10,
                          **kw)

        plot.y_axis.title_spacing = 50
        return plot

    # private
    def _create(self, evt):
        self.reset()

        g = self.isotope_graph
        self.selected_graph = g

        for _ in self.detectors:
            self._new_plot()
        evt.set()

    def _get_ncounts(self):
        return self._ncounts

    def _set_ncounts(self, v):

        o = self._ncounts

        self.info('{} set to terminate after {} counts'.format(self.plot_title, v))
        self._ncounts = v

        xmi, xma = self.isotope_graph.get_x_limits()
        xm = max(xma, xma + (v - o) * 1.05)
        self.isotope_graph.set_x_limits(max_=xm)

    def _get_ncycles(self):
        return self._ncycles

    def _set_ncycles(self, v):
        self.info('{} set to terminate after {} ncycles'.format(self.plot_title, v))
        self._ncycles = v

        if self.hops:
            # update ncounts
            integration_time = 1.1
            counts = sum([ci * integration_time + s for _h, ci, s in self.hops]) * v
            self._ncounts = counts

    def _get_display_counts(self):
        return 'Current: {:03d}'.format(self.counts)

    def _graph_factory(self):
        return StackedRegressionGraph(container_dict=dict(padding=5, bgcolor='gray',
                                                          stack_order=self.stack_order,
                                                          spacing=5),
                                      bind_index=False,
                                      use_data_tool=False,
                                      padding_bottom=35)

    # ===============================================================================
    # handlers
    # ===============================================================================
    @on_trait_change('isotope_graph, peak_center_graph')
    def _update_graphs(self):
        if self.isotope_graph and self.peak_center_graph:
            g, p = self.isotope_graph, self.peak_center_graph

            g.page_name = 'Isotopes'
            p.page_name = 'Peak Center'
            self.graphs = [g, p]

    def _plot_title_changed(self, new):
        self.graph_container.label = new

    @on_trait_change('isotope_graph:regression_results')
    def _update_display(self, obj, name, old, new):
        if new:
            self.analysis_view.load_computed(self.arar_age, new_list=False)
            self.analysis_view.refresh_needed = True

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _isotope_graph_default(self):
        return self._graph_factory()

    def _graph_container_default(self):
        self.isotope_graph.page_name = 'Isotopes'
        self.peak_center_graph.page_name = 'Peak Center'

        return GraphContainer(model=self)

    def _graphs_default(self):
        return [self.isotope_graph, self.peak_center_graph]

# ============= EOF =============================================
