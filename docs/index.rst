|made-with-python| |Documentation Status| |GitHub license|

fit2gpx -- convert .fit to .gpx
===============================

This is a simple Python library for converting .FIT files to .GPX files.
It also includes tools to convert Strava data downloads in bulk to GPX.
- `FIT <https://developer.garmin.com/fit/overview/>`__ is a GIS data
file format used by Garmin GPS sport devices and Garmin software -
`GPX <https://docs.fileformat.com/gis/gpx/>`__ is an XML based format
for GPS tracks.

When: Use Cases
===============

1. You need to convert .FIT files to pandas dataframe
2. You need to convert .FIT files to .GPX
3. You need to fix files dowloaded from Strava by converting the raw
   .FIT files to their .GPX counterparts

Why
===

Motivation
^^^^^^^^^^

I decided to create this package after spending a few hours searching
for a simple solution to quickly convert hundreds of FIT files to GPX. I
needed to do this as GIS applications do not parse FIT files. Whilst a
few solutions existed, they are command line scripts which offered very
little flexibility.

Relevance to Strava
^^^^^^^^^^^^^^^^^^^

-  Pre-GPDR, you could bulk export all your Strava activities as GPX
   files.
-  Post-GDPR, you can export an archive of your account. Whilst this
   includes much more data, activity GPS files are now downloaded in
   their original file format (eg. GPX or FIT format, some gzipped, some
   not) and named like 2500155647.gpx, 2500155647.gpx.gz,
   2500155647.fit, and 2500155647.fit.gz.
-  `How to bulk export you Strava
   Data <https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export#Bulk>`__

Overview
========

The fit2gpx module provides two converter classes: - Converter: used to
convert a single or multiple FIT files to pandas dataframes or GPX files
- StravaConverter: used to fix all the Strava Bulk Export problems in
three steps: 1. Unzip GPX and FIT files 2. Add activity metadata to
existing GPX files 3. Convert FIT files to GPX including activity
metadata from Strava)

Use Case 1: FIT to pd.DataFrame
===============================

Step 1: Import module and create converter object

.. code:: python

    from fit2gpx import Converter

    conv = Converter()

Step 2: Convert FIT file to 2 pd.DataFrame: fit\_to\_dataframes()

.. code:: python

    df_lap, df_point = conv.fit_to_dataframes(fname='3323369944.fit')

-  df\_points: information per track point: longitude, latitude,
   altitude, timestamp, heart rate, cadence, speed
-  df\_laps: information per lap: lap number, start time, total
   distance, total elapsed time, max speed, max heart rate, average
   heart rate

Use Case 2: FIT to GPX
======================

Import module and create converter object

.. code:: python

    from fit2gpx import Converter

    conv = Converter()          # create standard converter object

Use case 2.1: convert a single fit file: fit\_to\_gpx()

.. code:: python

    gpx = conv.fit_to_gpx(f_in='3323369944.fit', f_out='3323369944.fit')

Use case 2.2: convert many fit files to gpx files: fit\_to\_gpx\_bulk()

.. code:: python

    conv.fit_to_gpx_bulk(dir_in='./project/activities/', dir_out='./project/activities_convert/')

Use Case 3: Strava Bulk Export Tools (FIT to GPX conversion)
============================================================

Copy the below code, adjusting the input directory (DIR\_STRAVA), to fix
the Strava Bulk Export problems discussed in the
`overview <#Overview>`__.

.. code:: python

    from fit2gpx import StravaConverter

    DIR_STRAVA = 'C:/Users/dorian-saba/Documents/Strava/'

    # Step 1: Create StravaConverter object 
    # - Note: the dir_in must be the path to the central unzipped Strava bulk export folder 
    # - Note: You can specify the dir_out if you wish. By default it is set to 'activities_gpx', which will be created in main Strava folder specified.

    strava_conv = StravaConverter(
        dir_in=DIR_STRAVA
    )

    # Step 2: Unzip the zipped files
    strava_conv.unzip_activities()

    # Step 3: Add metadata to existing GPX files
    strava_conv.add_metadata_to_gpx()

    # Step 4: Convert FIT to GPX
    strava_conv.strava_fit_to_gpx()

Dependencies
============

pandas
^^^^^^

`pandas <https://github.com/pandas-dev/pandas>`__ is a Python package
that provides fast, flexible, and expressive data structures designed to
make working with "relational" or "labeled" data both easy and
intuitive. #### gpxpy `gpxpy <https://github.com/tkrajina/gpxpy>`__ is a
simple Python library for parsing and manipulating GPX files. It can
parse and generate GPX 1.0 and 1.1 files. The generated file will always
be a valid XML document, but it may not be (strictly speaking) a valid
GPX document. #### fitdecode
`fitdecode <https://github.com/polyvertex/fitdecode>`__ is a rewrite of
the `fitparse <https://github.com/dtcooper/python-fitparse>`__ module
allowing to parse ANT/GARMIN FIT files.

.. |made-with-python| image:: https://img.shields.io/badge/Made%20with-Python-1f425f.svg
   :target: https://www.python.org/
.. |Documentation Status| image:: https://readthedocs.org/projects/fit2gpx/badge/?version=latest
   :target: https://fit2gpx.readthedocs.io/en/latest/?badge=latest
.. |GitHub license| image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: https://www.gnu.org/licenses/gpl-3.0
