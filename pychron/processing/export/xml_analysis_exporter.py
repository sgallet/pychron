# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Instance
# ============= standard library imports ========================
import base64
import struct
import os
# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
from pychron.processing.export.destinations import XMLDestination
from pychron.processing.export.export_spec import MassSpecExportSpec, XMLExportSpec
from pychron.processing.export.exporter import Exporter


class XMLAnalysisExporter(Exporter):
    destination = Instance(XMLDestination, ())

    def __init__(self, *args, **kw):
        super(XMLAnalysisExporter, self).__init__(*args, **kw)
        from pychron.core.xml.xml_parser import XMLParser

        xmlp = XMLParser()
        self._parser = xmlp

    def set_destination(self, destination):
        self.destination = destination

    def _make_spec(self, ai):
        rs_name, rs_text = '', ''
        rid = ai.record_id
        exp = XMLExportSpec(runid=rid,
                            runscript_name=rs_name,
                            runscript_text=rs_text,
                            mass_spectrometer=ai.mass_spectrometer.capitalize(),
                            isotopes=ai.isotopes)

        exp.load_record(ai)
        return exp

    def add(self, analysis):
        spec = self._make_spec(analysis)
        # if not isinstance(spec, MassSpecExportSpec):
        # s = MassSpecExportSpec()
        # s.load_record(spec)
        #     spec = s

        self._make_xml_analysis(self._parser, spec)
        return True

    def start_export(self):
        isdir = os.path.isdir(os.path.dirname(self.destination.destination))
        if not isdir:
            self.warning_dialog('Invalid destination. {} does not exist'.format(isdir))
        return isdir

    def export(self):
        if os.path.isdir(os.path.dirname(self.destination.destination)):
            self._parser.save(self.destination.destination)

    def _make_timeblob(self, t, v):
        blob = ''
        for ti, vi in zip(t, v):
            blob += struct.pack('>ff', float(vi), float(ti))
        return blob

    def _make_xml_analysis(self, xmlp, spec):
        vertag = xmlp.add('version', '', None)
        xmlp.add('ver', '0.1', vertag)
        xmlp.add('encoding', 'RFC3548-Base64', vertag)
        xmlp.add('endian', 'big', vertag)
        xmlp.add('format', 'ff', vertag)

        an = xmlp.add('analysis', '', None)
        meta = xmlp.add('metadata', '', an)

        for attr in ('labnumber', 'aliquot', 'step', 'timestamp',
                     'power_requested',
                     'power_achieved',
                     'duration',
                     'duration_at_request',
                     'cleanup',
                     'runscript_name',):
            xmlp.add(attr, getattr(spec, attr), meta)

        irrad = xmlp.add('Irradiation', '', an)
        xmlp.add('name', spec.irradiation, irrad)
        xmlp.add('level', spec.level, irrad)
        xmlp.add('position', spec.irradiation_position, irrad)

        chron = xmlp.add('chronology', '', irrad)
        for power, start, end in spec.chron_dosages:
            dose = xmlp.add('dose', '', chron)
            xmlp.add('power', power, dose)
            xmlp.add('start', start, dose)
            xmlp.add('end', end, dose)

        pr = xmlp.add('production_ratios', '', irrad)
        xmlp.add('production_name', spec.production_name, pr)
        for d in (spec.production_ratios, spec.interference_corrections):
            for pname, pv in d.iteritems():
                pp = xmlp.add(pname, '', pr)
                xmlp.add('value', nominal_value(pv), pp)
                xmlp.add('error', std_dev(pv), pp)

        isostag = xmlp.add('isotopes', '', an)
        for isotope in spec.isotopes.itervalues():
            isok = isotope.name
            det = isotope.detector
            sfit = isotope.fit

            isotag = xmlp.add(isok, '', isostag)

            xmlp.add('detector', det, isotag)
            xmlp.add('fit', sfit, isotag)
            xmlp.add('intercept_value', nominal_value(isotope.uvalue), isotag)
            xmlp.add('intercept_error', std_dev(isotope.uvalue), isotag)

            baseline = isotope.baseline
            xmlp.add('baseline_value', nominal_value(baseline.uvalue), isotag)
            xmlp.add('baseline_error', std_dev(baseline.uvalue), isotag)

            blank = isotope.blank
            xmlp.add('blank_value', nominal_value(blank.uvalue), isotag)
            xmlp.add('blank_error', std_dev(blank.uvalue), isotag)

            datatag = xmlp.add('raw', '', isotag)

            xmlp.add('signal',
                     base64.b64encode(self._make_timeblob(isotope.offset_xs,
                                                          isotope.ys)), datatag)

            xmlp.add('baseline',
                     base64.b64encode(self._make_timeblob(baseline.xs,
                                                          baseline.ys)), datatag)


# ============= EOF =============================================



