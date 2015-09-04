# !Measurement
'''
'''
# counts
MULTICOLLECT_COUNTS = 4

# baselines
BASELINE_COUNTS = 2
BASELINE_DETECTOR = 'H1'
BASELINE_MASS = 39.5
BASELINE_BEFORE = False
BASELINE_AFTER = True

# peak center
PEAK_CENTER_BEFORE = False
PEAK_CENTER_AFTER = False
PEAK_CENTER_DETECTOR = 'H1'
PEAK_CENTER_ISOTOPE = 'Ar40'


# equilibration
EQ_TIME = 2
INLET = 'R'
OUTLET = 'S'
DELAY = 3.0
TIME_ZERO_OFFSET = 5

# PEAK HOP
USE_PEAK_HOP = False
PEAK_HOPS = [((('Ar40', 'H1'), 'CDD'), 10),
           ((('Ar39', 'CDD')), 10),
           ((('Ar38', 'CDD')), 10),
           ((('Ar37', 'CDD')), 10),
           ]
ACTIVE_DETECTORS = ('H1', 'AX')
FITS = [
      ((0, 5), ('linear', 'linear')),
      ((5, None), ('linear', 'parabolic'))
      ]
# FITS=('linear','linear')

ACTIONS = [(False, ('age', '<', 10.6, 20, 10, '', False)),
          ]

TRUNCATIONS = [(False, ('age', '<', 10.6, 20, 10,)),
              ]

TERMINATIONS = [(False, ('age', '<', 10.6, 20, 10))
              ]


def main():
    # this is a comment
    '''
        this is a multiline 
        comment aka docstring
    '''
    # display information with info(msg)
    info('unknown measurement script')

    # set the spectrometer parameters
    # provide a value
    set_source_parameters(YSymmetry=10)

    # or leave blank and values are loaded from a config file (setupfiles/spectrometer/config.cfg)
    set_source_optics()

    # set the cdd operating voltage
    set_cdd_operating_voltage(100)

    if PEAK_CENTER_BEFORE:
        peak_center(detector=PEAK_CENTER_DETECTOR, isotope=PEAK_CENTER_ISOTOPE)

    # open a plot panel for this detectors
    activate_detectors(*ACTIVE_DETECTORS)

    if BASELINE_BEFORE:
        baselines(ncounts=BASELINE_COUNTS, mass=BASELINE_MASS, detector=BASELINE_DETECTOR)
    # set default regression
    regress(*FITS)

    # position mass spectrometer
    position_magnet('Ar40', detector='H1')

    # gas is staged behind inlet

    # post equilibration script triggered after eqtime elapsed
    # equilibrate is non blocking
    # so use either a sniff of sleep as a placeholder until eq finished
    equilibrate(eqtime=EQ_TIME, inlet=INLET, outlet=OUTLET)

    for use, args in ACTIONS:
        if use:
            add_action(*args)

    for use, args in TRUNCATIONS:
        if use:
            add_truncation(*args)

    for use, args in TERMINATIONS:
        if use:
            add_termination(*args)

    # equilibrate returns immediately after the inlet opens
    set_time_zero(offset=TIME_ZERO_OFFSET)

    sniff(EQ_TIME)

    if USE_PEAK_HOP:
        '''
            
            hop = (Isotope, DetA)[,DetB,DetC...], counts
            
            ex. 
            hops=[((('Ar40','H1'),'CDD'),  10),
                  ((('Ar39','CDD')),       30), 
            
        '''
        peak_hop(hops=PEAK_HOPS)
    else:
        # multicollect on active detectors
        multicollect(ncounts=MULTICOLLECT_COUNTS, integration_time=1)

    clear_conditions()

    if BASELINE_AFTER:
        baselines(ncounts=BASELINE_COUNTS, mass=BASELINE_MASS, detector=BASELINE_DETECTOR)
    if PEAK_CENTER_AFTER:
        peak_center(detector=PEAK_CENTER_DETECTOR, isotope=PEAK_CENTER_ISOTOPE)

    info('finished measure script')

# ========================EOF==============================================================
    # peak_hop(detector='CDD', isotopes=['Ar40','Ar39','Ar36'], cycles=2, integrations=3)
    # baselines(counts=50,mass=0.5, detector='CDD')s

# isolate sniffer volume
    # close('S')
#     sleep(1)
#
#     #open to mass spec
#     open('R')
#
#     set_time_zero()
#     #display pressure wave
#     sniff(5)
#
#     #define sniff/split threshold
#     sniff_threshold=100
#
#     #test condition
#     #if get_intensity('H1')>sniff_threshold:
#     if True:
#         gosub('splits:jan_split', klass='ExtractionLinePyScript')
#
