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
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.pychron_constants import LINE_STR, ALPHAS

ANALYSIS_MAPPING = dict(ba='Blank Air', bc='Blank Cocktail', bu='Blank Unknown',
                        bg='Background', u='Unknown', c='Cocktail', a='Air',
                        pa='Pause'
)

# "labnumbers" where extract group is disabled
NON_EXTRACTABLE = dict(ba='Blank Air', bc='Blank Cocktail', bu='Blank Unknown',
                       bg='Background', c='Cocktail', a='Air'
)

SPECIAL_NAMES = ['Special Labnumber', LINE_STR, 'Air', 'Cocktail', 'Blank Unknown',
                 'Blank Air', 'Blank Cocktail', 'Background', 'Pause', 'Degas']

SPECIAL_MAPPING = dict(background='bg', air='a', cocktail='c',
                       blank_air='ba',
                       blank_cocktail='bc',
                       blank_unknown='bu',
                       pause='pa',
                       degas='dg'
)
#        sn = ['Blank_air', 'Blank_cocktail', 'Blank_unknown',
#              'Background', 'Air', 'Cocktail']
# SPECIAL_IDS = {1:'Blank Air', 2:'Blank Cocktail', 3:'Blank Unknown',
#               4:'Background', 5:'Air', 6:'Cocktail'
#               }

from ConfigParser import ConfigParser
import os
from pychron.paths import paths

cp = ConfigParser()
p = os.path.join(paths.setup_dir, 'identifiers.cfg')
if os.path.isfile(p):
    cp.read(p)
    for option in cp.options('AnalysisNames'):
        v = cp.get('AnalysisNames', option)
        labnumber, kname = v.split(',')
        ANALYSIS_MAPPING[option] = kname
        SPECIAL_NAMES.append(kname)
        SPECIAL_MAPPING[kname] = option

#        SPECIAL_IDS[int(labnumber)] = name

def convert_special_name(name, output='shortname'):
    '''
        input name output shortname
        
        name='Background'
        returns:
            
            if output=='shortname'
                return 'bg'
            else
                return 4 #identifier
    '''
    if isinstance(name, str):
        name = name.lower()
        name = name.replace(' ', '_')

        if name in SPECIAL_MAPPING:
            sn = SPECIAL_MAPPING[name]
            if output == 'labnumber':
                sn = convert_identifier(sn)
            return sn
    else:
        return name


def convert_identifier(identifier):
    '''
        old:
            identifier=='bg, a, ...'
            return  1
        
        identifier== bu-FD-J, 51234, 13212-01
        return bu-FD-J, 51234, 13212
        
    '''
    if '-' in identifier:
        ln = identifier.split('-')[0]
        try:
            ln = int(ln)
            identifier = str(ln)
        except ValueError:
            return identifier

            #        identifier=identifier.split('-')[0]


            #    if identifier in ANALYSIS_MAPPING:
            #        sname = ANALYSIS_MAPPING[identifier]
            #        identifier = next((k for k, v in SPECIAL_IDS.iteritems() if v == sname), identifier)

    return identifier


def get_analysis_type(idn):
    idn = idn.lower()

    #     if '-' in idn:
    #         idn=idn.split('-')[0]
    #
    # check for Bg before B
    if idn.startswith('bg'):
        return 'background'
    elif idn.startswith('ba'):
        return 'blank_air'
    elif idn.startswith('bu'):
        return 'blank_unknown'
    elif idn.startswith('bc'):
        return 'blank_cocktail'
    elif idn.startswith('a'):
        return 'air'
    elif idn.startswith('c'):
        return 'cocktail'
    elif idn.startswith('dg'):
        return 'degas'
    elif idn.startswith('pa'):
        return 'pause'
    else:
        return 'unknown'


def make_runid(ln, a, s=''):
    _as = make_aliquot_step(a, s)
    return '{}-{}'.format(ln, _as)


def strip_runid(r):
    l, x = r.split('-')

    a = ''
    for i, xi in enumerate(x):
        a += xi
        try:
            int(a)
        except ValueError:
            a = x[:i]
            s = x[i:]
            break
    else:
        s = ''

    return l, int(a), s


def make_step(s):
    if isinstance(s, (float, int, long)):
        s = ALPHAS[int(s)]
    return s or ''


def make_aliquot_step(a, s):
    if not isinstance(a, str):
        a = '{:02n}'.format(int(a))
    s = make_step(s)
    return '{}{}'.format(a, s)


def make_identifier(ln, ed, ms):
    try:
        _ = int(ln)
        return ln
    except ValueError:
        return make_special_identifier(ln, ed, ms)


def make_standard_identifier(ln, modifier, ms, aliquot=None):
    """
        ln: str or int
        a: int
        modifier: str or int. if int zero pad
        ms: int or str
    """
    if isinstance(ms, int):
        ms = '{:02n}'.format(ms)
    try:
        modifier = '{:02n}'.format(modifier)
    except ValueError:
        pass

    d = '{}-{}-{}'.format(ln, modifier, ms)
    if aliquot:
        d = '{}-{:02n}'.format(d, aliquot)
    return d


def make_special_identifier(ln, ed, ms, aliquot=None):
    """
        ln: str or int
        a: int aliquot
        ms: int mass spectrometer id
        ed: int extract device id
    """
    if isinstance(ed, int):
        ed = '{:02n}'.format(ed)
    if isinstance(ms, int):
        ms = '{:02n}'.format(ms)

    d = '{}-{}-{}'.format(ln, ed, ms)
    if aliquot:
        if not isinstance(aliquot, str):
            aliquot = '{:02n}'.format(aliquot)

        d = '{}-{}'.format(d, aliquot)
    return d


def make_rid(ln, a, step=''):
    """
        if ln can be converted to integer return runid
        else return ln-a
    """
    try:
        _ = int(ln)
        return make_runid(ln, a, step)
    except ValueError:
        if not isinstance(a, str):
            a = '{:02n}'.format(a)
        return '{}-{}'.format(ln, a)


def is_special(ln):
    special = False
    if '-' in ln:
        special = ln.split('-')[0] in ANALYSIS_MAPPING
    return special

#        return make_special_identifier(ln, ed, ms, aliquot=a)
#===============================================================================
# deprecated
#===============================================================================
SPECIAL_IDS = {1: 'Blank Air', 2: 'Blank Cocktail', 3: 'Blank Unknown',
               4: 'Background', 5: 'Air', 6: 'Cocktail'
}
# @deprecated
def convert_labnumber(ln):
    """
        ln is a str  but only special labnumbers cannot be converted to int
        convert number to name

    """
    try:
        ln = int(ln)

        if ln in SPECIAL_IDS:
            ln = SPECIAL_IDS[ln]
    except ValueError:
        pass

    return ln


# @deprecated
def convert_shortname(ln):
    """
        convert number to shortname (a for air, bg for background...)
    """
    name = convert_labnumber(ln)
    if name is not None:
        ln = next((k for k, v in ANALYSIS_MAPPING.iteritems()
                   if v == name), ln)
    return ln


def convert_extract_device(name):
    """
        change Fusions UV to fusions_uv, etc
    """
    n = ''
    if name:
        n = name.lower().replace(' ', '_')
    return n


def pretty_extract_device(ident):
    """
        change fusions_uv to Fusions UV, etc
    """
    n = ''
    if ident:
        args = ident.split('_')
        if args[-1] in ('uv, co2'):
            n = ' '.join(map(str.capitalize, args[:-1]))
            n = '{} {}'.format(n, args[-1].upper())
        else:
            n = ' '.join(map(str.capitalize, args))
            #n=ident.replace(' ', '_')
    return n

#============= EOF =============================================
