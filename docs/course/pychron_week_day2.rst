Pychron Week Day 2. Browsing
==============================

Review Day 1.
    1. go to documentation
    2. launch pychron
    3. submit issues
    4. submit notes

New feature
    1. User/Session Login
    2. Frequency templates
    3. Email group



Browser
------------------------
    1. By Project
    2. By Irradiation
    3. Graphical Filter
    4. Subfilters
    5. Filtering results
    6. Manual Queries

Browsing is a convenient way of navigating the pychron database. It is similar to Mass Spec's recall/run
selection window's however pychron's browser pane has the most commonly used query's predefined and organized
into a simple workflow.

.. note:: If the **Browser** is not open, go to View/Browser. If ``Browser`` is not present then the active window does not support
          the **Browser** and you must open a window that uses it e.g. **Recall**

The browser is laid out in a top down fashion and divided into multiple levels.
    1. Mass Spectrometer
    2. a) Identifier
       b) Projects
       c) Irradiations
    3. Analysis Types
    4. Date
    5. Results
      a) Sample/Identifier (L#)
      b) Analyses

Filters from the upper levels cascade down to the lower levels. For example selecting Mass Spectrometer=Obama
limits the Projects list to projects that contain analyses from Obama. The same filtering is applied to the
Irradiation list.

.. note:: Use the |binoc| button to force a refresh using the current filtering criteria.

.. |binoc| image:: ../images/find.png

Browser By Identifier
~~~~~~~~~~~~~~~~~~~~~~
Enter at least first three digits to browser by Identifier (aka L#). For example 210
will populate the Samples table with all Identifiers that start with 210.

Browse By Project
~~~~~~~~~~~~~~~~~~~~
The **Projects** table lists all projects currently in the database.

.. note:: For faster/easier searching of the **Project** table use the **Filter** textbox to limit the displayed projects to projects that begin with the filtering string.
   e.g. filter='abc' projects='abc', 'abcd', 'abcd12' but not '1abc'

.. note:: There are a few special projects listed in the **Projects** table. These are the **RECENT ...** entries, one for each mass spectrometer in the database. Selecting a **RECENT** entry
    will select all samples that have been run within the last *X* hours. To set *X* go to Preferences/Processing/Recent

.. note:: Selecting Projects filters the Irradiation list.

Browser By Irradiation
~~~~~~~~~~~~~~~~~~~~~~~~
Use the Irradiations drop-downs to filter the available samples by irradiation and irradiation level.

.. note:: Selecting an Irradiation Level i.e. "A" filters the Project list.

Subfilters
~~~~~~~~~~~~~~~~
The results from the upper level filters can be further refined with Analysis Type and Date Filters

.. note:: You do not have to start with the top level filters. For example you can start with a Date filter.

Results Tables
~~~~~~~~~~~~~~~~
The results of the filters are displayed in two tables Samples and Analyses. The Samples table
displays all the labnumbers that match your query. Select a set of labnumbers and the Analyses table will
display all the analyses for those labnumbers.

Both the Samples and Analyses tables are filterable. Use the dropdowns to select the attribute to filter on
then enter a value or select from available options.

.. note:: To configure what columns are displayed hit the |cog| button.

.. warning:: By default only labnumbers that have analyses are displayed. To show all labnumbers deselect
   "Exclude Non-run" in the configure dialog (hit the |cog| button)

.. warning:: By default only 100 analyses are displayed in the Analyses table. Use the |cog| button
   to set the results limit.

Switching Focus
~~~~~~~~~~~~~~~~~~~~
Pychron can switch focus between a filter dominant view and a results dominant view.
To enable focus switching use the check box at the top middle of the Browser pane.
To switch to results view select a row in the Sample table. To toggle between views
use the |switch| button.

.. |switch| image:: ../images/arrow_switch.png


Recall
-------------------------
Recall an analysis by double clicking on it in the Analyses table. All tasks windows
support opening a recall tab, however for simple viewing of analyses use Data>Recall or File>Recall (CMD+R).
This will open the Recall task

Find References
~~~~~~~~~~~~~~~~~
To find a set of reference analyses that are near the current analysis (currently hardcored as +/-4 hours),
right click an analysis in the Analyses table and select Find References

Configure
~~~~~~~~~~~~~~~~
To configure the recall view use the Configure Recall (|cog|) action. This will open a dialog that allows
you to set font sizes and define what information is displayed.

Isotope Evolutions
~~~~~~~~~~~~~~~~~~~~
Use Iso Fit |iso_evo| to open graphs of the isotope evolutions in a separate tab. You can also
right click on a set of isotope rows and pop up a standalone iso evo graph.

Edit Data
~~~~~~~~~~~~~
To manual edit isotope values, e.g. intensities, blanks use Edit Data (|edit|).

Diff Analyses
~~~~~~~~~~~~~~~
Use the Diff |diff| button to open the Analysis diff tab. This tab is used to systematically
compare a Pychron analysis to a Mass Spec analysis. This tab displays a Pychron-Diff-MassSpec
table.

.. note:: By default only the differences between the analyses are displayed

Summary L# View
~~~~~~~~~~~~~~~~~
The Summary L# View |sum_view| provides three summary views

    1. Stats
    2. Ideogram
    3. Spectrum

To display, select a row in the Samples table, then hit |sum_view|

Context View
~~~~~~~~~~~~~~~~
Context View displays a table of values for analyses that bracket the selected analysis.
Tabular and graphical views are displayed. To populate the graphical view select a set of
analyses from the tabular view.

Subviews
~~~~~~~~~~~~~~~~~
The recall window provides additional information in subviews. to switch
to different views use the Controls pane. When a recall tab is selected
Controls will display a list of subviews. The list depends on the type of analysis.



Plotting
-------------------------
To make figures open any open of the Figure Tasks, for example Data>Ideogram.

Figure Tasks introduce an new important pane, the "Unknowns" pane. this pane
holds the list of analyses to plot. There are several ways to load analyses
into the Unknowns pane.

Use the browser to select a set of analyses.

    1. If you want to plot all analyses from a L# double click it and it will be added to the Unknowns Pane.
    2. If you want to plot a set of L#'s select the set and right click and choose Plot Selected or Plot Selected(Grouped). Plot Selected(Grouped) will group the analyses by L#.
    3. If you want to plot a set of analyses select them and
     a) Use the append/replace button in the Unknowns Pane
     b) Right click and use append or replace
     c) drag the analyses into the unknowns pane

.. |sum_view| image:: ../images/window-new.png
.. |iso_evo| image:: ../images/chart_curve_add.png
.. |diff| image:: ../images/edit_diff.png
          :height: 16px
          :width: 16px
.. |edit| image:: ../images/application-form-edit.png
.. |cog| image:: ../images/cog.png